"""管理员 API."""
import json

from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import admin_required, bump_token_version, get_request_user_id, write_audit
from app.middleware.entitlement import paywall_response
from app.models import AiUsageLog, Classroom, BehaviorLog, GroupInfo, PaymentOrder, Task, TeamActivity, User, UserProfile, UserSubscription
from app.services.billing_service import mark_order_paid, pending_review_count, refresh_order_lifecycle
from app.services.entitlement_service import PaywallError, activate_subscription, get_entitlements
from app.services.task_ai_helpers import enrich_adjust_with_ai, enrich_assignments_with_ai
from app.services.algorithms.grouping import GroupingAlgorithm
from app.services.algorithms.task_adjust import TaskAdjustAlgorithm
from app.services.algorithms.task_assign import TaskAssignAlgorithm
from app.services.analytics_service import build_group_dashboard, build_platform_dashboard
from app.services.group_config import load_group_config, set_member_roles
from app.services.role_assign import assign_roles_for_group
from app.services.class_membership import filter_user_ids, restrict_to_class_members
from app.services.task_service import create_assigned_tasks
from app.services.teacher_scope import admin_owns_class, teacher_classroom_query

bp = Blueprint("admin", __name__)
group_algo = GroupingAlgorithm()
assigner = TaskAssignAlgorithm()
adjuster = TaskAdjustAlgorithm()


@bp.route("/users", methods=["GET", "POST"])
@admin_required
def users_collection():
    if request.method == "POST":
        return _create_user()
    return _list_users()


def _list_users():
    exclude_demo = request.args.get("exclude_demo", "1") in ("1", "true", "yes")
    include_demo = request.args.get("include_demo", "0") in ("1", "true", "yes")
    include_profile = request.args.get("include_profile", "0") in ("1", "true", "yes")
    limit = min(int(request.args.get("limit", 200) or 200), 500)
    offset = max(int(request.args.get("offset", 0) or 0), 0)
    q = User.query
    if exclude_demo and not include_demo:
        q = q.filter((User.is_demo == False) | (User.is_demo.is_(None)))  # noqa: E712
    total = q.count()
    users = q.order_by(User.id.asc()).offset(offset).limit(limit).all()
    user_ids = [u.id for u in users]
    profiles = {}
    if user_ids:
        for prof in UserProfile.query.filter(UserProfile.user_id.in_(user_ids)).order_by(
            UserProfile.user_id.asc(), UserProfile.create_time.desc()
        ).all():
            if prof.user_id not in profiles:
                profiles[prof.user_id] = prof
    data = []
    for u in users:
        prof = profiles.get(u.id)
        data.append(
            {
                "user": u.to_dict(),
                "has_profile": prof is not None,
                "profile": prof.to_dict() if prof and include_profile else None,
            }
        )
    return jsonify({"items": data, "total": total, "limit": limit, "offset": offset})


def _create_user():
    import bcrypt

    from app.services.auth_verification import validate_account_name, validate_password_strength

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    account = (data.get("account") or data.get("email") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "user").strip()
    if role not in {"user", "admin"}:
        return jsonify({"error": "角色无效"}), 400
    if not name:
        return jsonify({"error": "姓名不能为空"}), 400
    acc_err = validate_account_name(account)
    if acc_err:
        return jsonify({"error": acc_err}), 400
    pw_err = validate_password_strength(password)
    if pw_err:
        return jsonify({"error": pw_err}), 400
    if User.query.filter_by(account=account).first():
        return jsonify({"error": "账号已存在"}), 400
    user = User(
        name=name,
        account=account,
        password_hash=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        role=role,
        is_demo=False,
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    write_audit("admin_create_user", "user", user.id, json.dumps({"role": role}, ensure_ascii=False))
    return jsonify({"user": user.to_dict()}), 201


@bp.route("/users/<int:user_id>", methods=["PATCH"])
@admin_required
def patch_user(user_id):
    """禁用/启用用户或重置密码."""
    import bcrypt

    target = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    if data.get("status") in ("active", "disabled"):
        target.status = data["status"]
        bump_token_version(target)
    new_password = (data.get("password") or "").strip()
    if new_password:
        from app.services.auth_verification import validate_password_strength

        pw_err = validate_password_strength(new_password)
        if pw_err:
            return jsonify({"error": pw_err}), 400
        target.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        bump_token_version(target)
    db.session.commit()
    write_audit("admin_patch_user", "user", target.id, json.dumps({"status": target.status}, ensure_ascii=False))
    return jsonify({"user": target.to_dict()})


@bp.route("/config", methods=["GET", "PUT"])
@admin_required
def system_config():
    from flask import current_app

    if request.method == "GET":
        return jsonify(
            {
                "default_group_size": current_app.config.get("DEFAULT_GROUP_SIZE", 4),
                "default_adjust_days": current_app.config.get("DEFAULT_ADJUST_DAYS", 7),
                "max_group_users": current_app.config.get("MAX_GROUP_USERS", 50),
            }
        )
    data = request.get_json(silent=True) or {}
    write_audit("admin_config", detail=json.dumps(data))
    return jsonify({"message": "配置已记录", "received": data})


@bp.route("/task-templates/market", methods=["GET"])
@admin_required
def task_template_market():
    """任务模板市场 — 一键应用子任务."""
    assigner = TaskAssignAlgorithm()
    catalog = []
    for key, tpl in (assigner.templates or {}).items():
        tasks = tpl.get("tasks") or tpl.get("default_tasks") or []
        catalog.append(
            {
                "key": key,
                "name": tpl.get("name") or key,
                "description": tpl.get("description") or "",
                "task_count": len(tasks),
                "sample_tasks": tasks[:4],
            }
        )
    return jsonify({"templates": catalog})


@bp.route("/templates", methods=["GET", "POST", "PUT"])
@admin_required
def manage_templates():
    assigner = TaskAssignAlgorithm()
    if request.method == "GET":
        return jsonify(assigner.templates)
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    if not key:
        return jsonify({"error": "key 必填"}), 400
    assigner.templates[key] = data.get("template", {})
    tpl_path = __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "task_templates.json"
    tpl_path.write_text(json.dumps(assigner.templates, ensure_ascii=False, indent=2), encoding="utf-8")
    write_audit("admin_template", detail=key)
    return jsonify(assigner.templates)


def _teacher_activity_ids(uid: int) -> list[int]:
    """当前教师可见班级下的组队活动 ID（GroupInfo 通过 activity_id 关联班级）."""
    class_ids = [c.id for c in teacher_classroom_query(uid).all()]
    if not class_ids:
        return []
    rows = TeamActivity.query.filter(TeamActivity.class_id.in_(class_ids)).with_entities(TeamActivity.id).all()
    return [r[0] for r in rows]


def _teacher_groups_query(uid: int, activity_id: int | None = None):
    class_ids = [c.id for c in teacher_classroom_query(uid).all()]
    groups_q = GroupInfo.query
    act_ids = _teacher_activity_ids(uid)
    if act_ids:
        groups_q = groups_q.filter(GroupInfo.activity_id.in_(act_ids))
    else:
        groups_q = groups_q.filter(GroupInfo.id == -1)
    if activity_id:
        groups_q = groups_q.filter_by(activity_id=activity_id)
    return groups_q, class_ids


@bp.route("/overview", methods=["GET"])
@admin_required
def overview():
    uid = get_request_user_id()
    groups = _teacher_groups_query(uid)[0].all()
    user_ids = set()
    for g in groups:
        user_ids.update(g.member_list())
    users = len([u for u in User.query.filter(User.id.in_(user_ids)).all() if u.role == "user" and not u.is_demo]) if user_ids else 0
    profiles = UserProfile.query.filter(UserProfile.user_id.in_(user_ids)).count() if user_ids else 0
    return jsonify(
        {
            "user_count": users,
            "profile_count": profiles,
            "group_count": len(groups),
            "groups": [g.to_dict() for g in groups],
        }
    )


def _dashboard_class_summaries(uid: int, *, limit: int = 8, include_nudge: bool = False):
    from app.services.classroom_insights import build_class_health, build_nudge_list

    class_summaries = []
    for cls in teacher_classroom_query(uid).order_by(Classroom.create_time.desc()).limit(limit).all():
        try:
            health = build_class_health(cls.id)
            nudge_total = 0
            if include_nudge:
                nudge_total = build_nudge_list(cls.id).get("total", 0)
            class_summaries.append(
                {
                    "class_id": cls.id,
                    "name": cls.name,
                    "health_score": health.get("health_score"),
                    "health_level": health.get("health_level"),
                    "nudge_total": nudge_total,
                    "pending_confirmations": health.get("pending_confirmations", 0),
                }
            )
        except Exception:
            pass
    return class_summaries


@bp.route("/dashboard/summary", methods=["GET"])
@admin_required
def command_dashboard_summary():
    """轻量指挥舱摘要（无逐组看板聚合）."""
    from app.services.analytics_service import assess_task_risk
    from datetime import datetime

    uid = get_request_user_id()
    activity_id = request.args.get("activity_id", type=int)
    groups_q, _class_ids = _teacher_groups_query(uid, activity_id)
    groups = groups_q.all()
    group_ids = [g.id for g in groups]
    tasks = Task.query.filter(Task.group_id.in_(group_ids)).all() if group_ids else []
    member_ids = set()
    for g in groups:
        member_ids.update(g.member_list())
    users = User.query.filter(User.id.in_(member_ids), User.role == "user").all() if member_ids else []
    profile_count = UserProfile.query.filter(UserProfile.user_id.in_(member_ids)).count() if member_ids else 0
    platform = build_platform_dashboard(groups, tasks, profile_count)
    now = datetime.utcnow()
    low_engagement = 0
    for t in tasks:
        td = t.to_dict()
        risk = assess_task_risk(td, now)
        if risk["level"] in ("critical", "warning") and int(td.get("progress") or 0) < 50:
            low_engagement += 1
    feedback_count = (
        BehaviorLog.query.filter(
            BehaviorLog.group_id.in_(group_ids),
            BehaviorLog.event_type == "task_feedback",
        ).count()
        if group_ids
        else 0
    )
    return jsonify(
        {
            "user_count": len(users),
            "profile_count": profile_count,
            "group_count": len(groups),
            "task_count": len(tasks),
            **platform,
            "low_engagement_members": low_engagement,
            "feedback_count": feedback_count,
            "class_summaries": _dashboard_class_summaries(uid, limit=8, include_nudge=False),
        }
    )


@bp.route("/dashboard/groups", methods=["GET"])
@admin_required
def command_dashboard_groups():
    """分页返回各组看板详情（按需加载）."""
    from app.api.board import _build_members_board

    uid = get_request_user_id()
    activity_id = request.args.get("activity_id", type=int)
    limit = min(int(request.args.get("limit", 20) or 20), 50)
    offset = max(int(request.args.get("offset", 0) or 0), 0)
    groups_q, _ = _teacher_groups_query(uid, activity_id)
    total = groups_q.count()
    groups = groups_q.order_by(GroupInfo.create_time.desc()).offset(offset).limit(limit).all()
    items = []
    for g in groups:
        members, task_dicts = _build_members_board(g)
        logs = BehaviorLog.query.filter_by(group_id=g.id).all()
        dash = build_group_dashboard(g.to_dict(), task_dicts, members, logs)
        items.append(dash)
    return jsonify({"items": items, "total": total, "limit": limit, "offset": offset})


@bp.route("/dashboard", methods=["GET"])
@admin_required
def command_dashboard():
    """指挥舱完整数据（兼容旧客户端；新前端请用 /dashboard/summary）."""
    uid = get_request_user_id()
    activity_id = request.args.get("activity_id", type=int)
    groups_q, _ = _teacher_groups_query(uid, activity_id)
    groups = groups_q.all()
    group_ids = [g.id for g in groups]
    tasks = Task.query.filter(Task.group_id.in_(group_ids)).all() if group_ids else []
    member_ids = set()
    for g in groups:
        member_ids.update(g.member_list())
    users = User.query.filter(User.id.in_(member_ids), User.role == "user").all() if member_ids else []
    profile_count = UserProfile.query.filter(UserProfile.user_id.in_(member_ids)).count() if member_ids else 0
    platform = build_platform_dashboard(groups, tasks, profile_count)
    low_engagement = 0
    feedback_count = 0
    try:
        from app.api.board import _build_members_board

        for g in groups[:30]:
            members, task_dicts = _build_members_board(g)
            logs = BehaviorLog.query.filter_by(group_id=g.id).all()
            dash = build_group_dashboard(g.to_dict(), task_dicts, members, logs)
            low_engagement += dash["summary"].get("low_engagement_members", 0)
            feedback_count += dash["summary"].get("feedback_count", 0)
    except Exception:
        pass
    return jsonify(
        {
            "user_count": len(users),
            "profile_count": profile_count,
            "group_count": len(groups),
            "task_count": len(tasks),
            **platform,
            "low_engagement_members": low_engagement,
            "feedback_count": feedback_count,
            "class_summaries": _dashboard_class_summaries(uid, limit=8, include_nudge=False),
        }
    )


@bp.route("/team/<int:group_id>/dashboard", methods=["GET"])
@admin_required
def admin_team_dashboard(group_id):
    from app.api.board import _build_members_board

    group = GroupInfo.query.get_or_404(group_id)
    members, task_dicts = _build_members_board(group)
    logs = BehaviorLog.query.filter_by(group_id=group_id).all()
    return jsonify(build_group_dashboard(group.to_dict(), task_dicts, members, logs))


@bp.route("/ops/create-groups", methods=["POST"])
@admin_required
def ops_create_groups():
    """批量智能分组."""
    from app.api.group import _profile_to_dict

    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    group_size = int(data.get("group_size", 4))
    mode = (data.get("config") or {}).get("mode", "heterogeneous")

    class_id = data.get("class_id")
    if class_id:
        user_ids = restrict_to_class_members(user_ids, int(class_id))
    else:
        user_ids = filter_user_ids(user_ids)
    if not user_ids:
        return jsonify({"error": "有效画像人数不足，无法分组"}), 400

    profiles = []
    for uid in user_ids:
        prof = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            profiles.append(_profile_to_dict(prof))

    if len(profiles) < group_size:
        return jsonify({"error": "有效画像人数不足，无法分组"}), 400

    result = group_algo.create_groups(profiles, group_size=group_size, mode=mode)
    saved = []
    for g in result["groups"]:
        gi = GroupInfo(
            group_name=g["group_name"],
            member_ids=json.dumps(g["member_ids"]),
            avg_knowledge=g["avg_knowledge"],
            avg_skill=g["avg_skill"],
            avg_collab=g["avg_collab"],
            balance_score=result["balance_score"],
            config=json.dumps(
                {
                    **result["config"],
                    "audit_log": result["audit_log"],
                    "complement_note": g.get("complement_note", ""),
                },
                ensure_ascii=False,
            ),
        )
        db.session.add(gi)
        saved.append(gi)
    db.session.commit()
    write_audit("admin_create_groups", detail=json.dumps({"count": len(saved)}))
    return jsonify({"groups": [g.to_dict() for g in saved], "balance_score": result["balance_score"]})


@bp.route("/ops/assign-tasks", methods=["POST"])
@admin_required
def ops_assign_tasks():
    """为小组分配项目任务."""
    from app.api.group import _profile_to_dict

    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    template_key = data.get("template_key", "product_dev")
    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    activity = TeamActivity.query.get(group.activity_id) if group.activity_id else None
    if activity and activity.status not in {"locked", "tasking", "adjusting", "completed"}:
        return jsonify({"error": "请先完成预沟通并锁定正式团队，再分配任务"}), 400
    members = []
    cfg = load_group_config(group)
    role_map = {int(r["user_id"]): r.get("role") for r in cfg.get("member_roles") or [] if r.get("user_id") is not None}
    for mid in group.member_list():
        prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            d = _profile_to_dict(prof)
            d["user_id"] = mid
            if role_map.get(int(mid)):
                d["pref_role"] = role_map[int(mid)]
            members.append(d)
    if not members:
        return jsonify({"error": "组内无有效画像"}), 400

    team_goal = data.get("team_goal") or (activity.task_goal if activity else "")
    assignments = assigner.assign(group_id, members, template_key, data.get("custom_tasks"), team_goal)
    ai_insight = None
    try:
        assignments, ai_insight = enrich_assignments_with_ai(
            get_request_user_id(),
            assignments,
            members,
            team_goal=team_goal,
            template_key=template_key,
            use_ai=bool(data.get("use_ai")),
        )
    except PaywallError as exc:
        return paywall_response(exc)
    created = create_assigned_tasks(group_id, assignments)
    if activity and activity.status == "locked":
        activity.status = "tasking"
    db.session.commit()
    write_audit("admin_assign_tasks", "group", group_id)
    return jsonify({"tasks": [t.to_dict() for t in created]})


@bp.route("/ops/assign-roles", methods=["POST"])
@admin_required
def ops_assign_roles():
    """为小组自动分配组内角色."""
    from app.api.group import _profile_to_dict

    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    profiles = []
    for mid in group.member_list():
        prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            d = _profile_to_dict(prof)
            d["user_id"] = mid
            profiles.append(d)

    if not profiles:
        return jsonify({"error": "组内无成员画像"}), 400

    roles = assign_roles_for_group(profiles)
    cfg = set_member_roles(group, roles)
    db.session.commit()
    write_audit("admin_assign_roles", "group", group_id)
    return jsonify({"group_id": group_id, "member_roles": cfg.get("member_roles", roles)})


@bp.route("/group/<int:group_id>/roles", methods=["PUT"])
@admin_required
def update_group_roles(group_id):
    """手动调整组内角色."""
    from datetime import datetime

    group = GroupInfo.query.get_or_404(group_id)
    data = request.get_json(silent=True) or {}
    updates = data.get("member_roles") or data.get("roles") or []

    cfg = load_group_config(group)
    existing = {int(r["user_id"]): r for r in cfg.get("member_roles") or [] if r.get("user_id") is not None}

    for item in updates:
        uid = int(item.get("user_id"))
        role = (item.get("role") or "").strip()
        if not role:
            continue
        existing[uid] = {
            "user_id": uid,
            "role": role,
            "source": "manual",
            "reason": item.get("reason") or "管理员手动调整",
            "assigned_at": datetime.utcnow().isoformat(),
        }

    roles = list(existing.values())
    cfg = set_member_roles(group, roles)
    db.session.commit()
    write_audit("admin_update_roles", "group", group_id)
    return jsonify({"group_id": group_id, "member_roles": cfg.get("member_roles", roles)})


@bp.route("/ops/assign-roles-all", methods=["POST"])
@admin_required
def ops_assign_roles_all():
    """为所有小组批量分配角色."""
    groups = GroupInfo.query.all()
    results = []
    for g in groups:
        if not g.member_list():
            continue
        from app.api.group import _profile_to_dict

        profiles = []
        for mid in g.member_list():
            prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
            if prof:
                d = _profile_to_dict(prof)
                d["user_id"] = mid
                profiles.append(d)
        if profiles:
            roles = assign_roles_for_group(profiles)
            set_member_roles(g, roles)
            results.append({"group_id": g.id, "group_name": g.group_name, "count": len(roles)})
    db.session.commit()
    write_audit("admin_assign_roles_all", detail=json.dumps({"groups": len(results)}))
    return jsonify({"groups": results})


@bp.route("/ops/adjust-tasks", methods=["POST"])
@admin_required
def ops_adjust_tasks():
    """触发动态任务调优."""
    from app.api.group import _profile_to_dict

    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    tasks = Task.query.filter_by(group_id=group_id).all()
    logs = BehaviorLog.query.filter_by(group_id=group_id).all()
    members = []
    for mid in group.member_list():
        prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            d = _profile_to_dict(prof)
            d["user_id"] = mid
            members.append(d)
    summary = adjuster.summarize_behavior(logs)
    task_dicts = [t.to_dict() for t in tasks]
    result = adjuster.adjust(task_dicts, summary, members)
    try:
        result = enrich_adjust_with_ai(
            get_request_user_id(),
            result,
            task_dicts,
            members,
            summary,
            use_ai=bool(data.get("use_ai")),
        )
    except PaywallError as exc:
        return paywall_response(exc)
    for t in tasks:
        for sug in result["suggestions"]:
            if sug.get("task_id") == t.id:
                t.pending_adjust = json.dumps(sug, ensure_ascii=False)
    activity = TeamActivity.query.get(group.activity_id) if group.activity_id else None
    if activity and activity.status == "tasking":
        activity.status = "adjusting"
    db.session.commit()
    write_audit("admin_adjust_tasks", "group", group_id)
    return jsonify(result)


_STATUS_LABELS = {
    "pending": "待支付",
    "pending_review": "待核销",
    "paid": "已支付",
    "expired": "已过期",
    "cancelled": "已取消",
}


@bp.route("/billing/orders", methods=["GET"])
@admin_required
def admin_billing_orders():
    """订单列表（运营核销）."""
    status = request.args.get("status")
    q = PaymentOrder.query.order_by(PaymentOrder.create_time.desc())
    if status:
        q = q.filter_by(status=status)
    rows = q.limit(200).all()
    users = {u.id: u for u in User.query.filter(User.id.in_([r.user_id for r in rows])).all()} if rows else {}
    data = []
    for o in rows:
        refresh_order_lifecycle(o)
        item = {
            **o.to_dict(include_qr=True),
            "status_label": _STATUS_LABELS.get(o.status, o.status),
            "user_name": users.get(o.user_id).name if users.get(o.user_id) else None,
            "user_account": users.get(o.user_id).account if users.get(o.user_id) else None,
        }
        data.append(item)
    return jsonify({"orders": data, "pending_review_count": pending_review_count()})


@bp.route("/billing/orders/<int:order_id>/fulfill", methods=["POST"])
@admin_required
def admin_fulfill_order(order_id):
    """人工核销订单."""
    order = PaymentOrder.query.get_or_404(order_id)
    refresh_order_lifecycle(order)
    data = request.get_json(silent=True) or {}
    try:
        mark_order_paid(order, remark=data.get("remark") or "admin_fulfill")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    write_audit("billing_fulfill", "payment_order", order.id)
    return jsonify({"message": "订单已核销", "order": order.to_dict(), "entitlements": get_entitlements(order.user_id)})


@bp.route("/billing/grant", methods=["POST"])
@admin_required
def admin_grant_subscription():
    """赠送套餐或延长订阅."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    plan_code = (data.get("plan_code") or "pro").strip()
    days = int(data.get("days") or 30)
    if not user_id:
        return jsonify({"error": "user_id 必填"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    period = "trial" if plan_code == "trial" else "month"
    activate_subscription(user_id, plan_code if plan_code != "trial" else "pro", period, days=days)
    write_audit("billing_grant", "user", user_id, json.dumps(data, ensure_ascii=False))
    return jsonify({"message": "已赠送权益", "entitlements": get_entitlements(user_id)})


@bp.route("/billing/usage", methods=["GET"])
@admin_required
def admin_billing_usage():
    """AI 用量与预估成本."""
    from sqlalchemy import func

    rows = (
        db.session.query(AiUsageLog.feature, func.count(AiUsageLog.id), func.sum(AiUsageLog.points_cost))
        .group_by(AiUsageLog.feature)
        .all()
    )
    total_points = sum(r[2] or 0 for r in rows)
    est_cost_cny = round(total_points * 0.01, 2)
    return jsonify(
        {
            "by_feature": [{"feature": r[0], "calls": r[1], "points": int(r[2] or 0)} for r in rows],
            "total_points": int(total_points),
            "estimated_api_cost_cny": est_cost_cny,
        }
    )
