"""管理员 API."""
import json

from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import admin_required, write_audit
from app.models import BehaviorLog, GroupInfo, Task, TeamActivity, User, UserProfile
from app.services.algorithms.grouping import GroupingAlgorithm
from app.services.algorithms.task_adjust import TaskAdjustAlgorithm
from app.services.algorithms.task_assign import TaskAssignAlgorithm
from app.services.analytics_service import build_group_dashboard, build_platform_dashboard
from app.services.group_config import load_group_config, set_member_roles
from app.services.role_assign import assign_roles_for_group
from app.services.task_service import create_assigned_tasks

bp = Blueprint("admin", __name__)
group_algo = GroupingAlgorithm()
assigner = TaskAssignAlgorithm()
adjuster = TaskAdjustAlgorithm()


@bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.all()
    data = []
    for u in users:
        prof = UserProfile.query.filter_by(user_id=u.id).order_by(UserProfile.create_time.desc()).first()
        data.append({"user": u.to_dict(), "has_profile": prof is not None, "profile": prof.to_dict() if prof else None})
    return jsonify(data)


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


@bp.route("/overview", methods=["GET"])
@admin_required
def overview():
    groups = GroupInfo.query.all()
    users = User.query.filter_by(role="user").count()
    profiles = UserProfile.query.count()
    return jsonify(
        {
            "user_count": users,
            "profile_count": profiles,
            "group_count": len(groups),
            "groups": [g.to_dict() for g in groups],
        }
    )


@bp.route("/dashboard", methods=["GET"])
@admin_required
def command_dashboard():
    """指挥舱：全平台预警与项目组健康度."""
    activity_id = request.args.get("activity_id", type=int)
    groups_q = GroupInfo.query
    if activity_id:
        groups_q = groups_q.filter_by(activity_id=activity_id)
    groups = groups_q.all()
    group_ids = [g.id for g in groups]
    tasks = Task.query.filter(Task.group_id.in_(group_ids)).all() if activity_id else Task.query.all()
    users = User.query.filter_by(role="user").all()
    profile_count = UserProfile.query.count()
    platform = build_platform_dashboard(groups, tasks, profile_count)
    low_engagement = 0
    feedback_count = 0
    try:
        from app.api.board import _build_members_board

        for g in groups:
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

    if not user_ids:
        users = User.query.filter_by(role="user").all()
        user_ids = [u.id for u in users]

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
    result = adjuster.adjust([t.to_dict() for t in tasks], summary, members)
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
