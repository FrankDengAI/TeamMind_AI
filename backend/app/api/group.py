"""分组 API."""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.models import GroupInfo, User, UserProfile
from app.services.algorithms.grouping import GroupingAlgorithm
from app.middleware.entitlement import paywall_response
from app.services.entitlement_service import PaywallError, get_entitlements
from app.services.grouping_templates import list_templates, resolve_template, template_to_group_config

bp = Blueprint("group", __name__)
algo = GroupingAlgorithm()


@bp.route("/templates", methods=["GET"])
@jwt_required()
def grouping_templates():
    uid = get_request_user_id()
    ent = get_entitlements(uid)
    return jsonify({"templates": list_templates(plan_code=ent.get("plan_code", "free"))})


def _profile_to_dict(prof: UserProfile) -> dict:
    d = prof.to_dict()
    d["user_id"] = prof.user_id
    return d


@bp.route("/create", methods=["POST"])
@admin_required
def create_groups():
    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    group_size = int(data.get("group_size", 4))
    config = data.get("config") or {}
    template_id = config.get("template_id") or data.get("template_id")
    if template_id:
        tpl = resolve_template(template_id)
        if tpl.get("tier") == "pro":
            ent = get_entitlements(get_request_user_id())
            if ent.get("plan_code") == "free":
                return jsonify({"error": "该分组模板需升级专业版", "code": "PAYWALL", "feature": "grouping.template"}), 402
        config = template_to_group_config(template_id, config)
    mode = config.get("mode", "heterogeneous")
    priority = config.get("priority", "skill")
    constraints = config.get("constraints") or {}

    if not user_ids:
        return jsonify({"error": "user_ids 不能为空"}), 400

    profiles = []
    for uid in user_ids:
        prof = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            profiles.append(_profile_to_dict(prof))

    if len(profiles) < group_size:
        return jsonify({"error": "有效画像人数不足"}), 400

    try:
        result = algo.create_groups(
            profiles,
            group_size=group_size,
            mode=mode,
            priority=priority,
            constraints=constraints,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

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
                {**result["config"], "audit_log": result["audit_log"], "complement_note": g["complement_note"]},
                ensure_ascii=False,
            ),
        )
        db.session.add(gi)
        saved.append(gi)
    db.session.commit()

    write_audit("group_create", "group", saved[0].id if saved else None, json.dumps({"count": len(saved)}))
    return jsonify(
        {
            "groups": [g.to_dict() for g in saved],
            "balance_score": result["balance_score"],
            "complement_notes": result["complement_notes"],
            "audit_log": result["audit_log"],
        }
    )


def _enrich_groups_for_ui(groups: list, profiles: list) -> list:
    users = {p["user_id"]: p for p in profiles}
    out = []
    for g in groups:
        members = []
        for mid in g.get("member_ids") or []:
            p = users.get(mid) or {}
            members.append(
                {
                    "user_id": mid,
                    "name": p.get("name") or User.query.get(mid).name if User.query.get(mid) else str(mid),
                    "major": p.get("major"),
                    "skill": p.get("skill_final") or p.get("skill_score"),
                    "pref_role": p.get("pref_role"),
                }
            )
        out.append(
            {
                "group_name": g["group_name"],
                "avg_skill": g["avg_skill"],
                "avg_knowledge": g.get("avg_knowledge"),
                "avg_collab": g.get("avg_collab"),
                "member_ids": g.get("member_ids"),
                "members": members,
                "complement_note": g.get("complement_note"),
            }
        )
    return out


@bp.route("/compare", methods=["POST"])
@admin_required
def compare_groups():
    """多方案分组对比（模板驱动，不写入 DB）."""
    from app.services.grouping_templates import GROUPING_TEMPLATES

    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    group_size = int(data.get("group_size", 4))
    template_ids = data.get("template_ids")
    uid = get_request_user_id()
    ent = get_entitlements(uid)
    if ent.get("plan_code") == "free":
        return jsonify({"error": "多方案对比需升级专业版", "code": "PAYWALL", "feature": "grouping.compare"}), 402
    try:
        from app.services.entitlement_service import check_limit

        check_limit(uid, "grouping_scenario_monthly", increment=1)
    except PaywallError as exc:
        return paywall_response(exc)

    profiles = []
    for u in user_ids:
        prof = UserProfile.query.filter_by(user_id=u).order_by(UserProfile.create_time.desc()).first()
        if prof:
            d = _profile_to_dict(prof)
            u = User.query.get(u)
            if u:
                d["name"] = u.name
            profiles.append(d)
    if len(profiles) < group_size:
        return jsonify({"error": "有效画像人数不足"}), 400

    tier_rank = {"free": 0, "pro": 1, "plus": 2}
    user_rank = tier_rank.get(ent.get("plan_code", "free"), 0)
    compare_tpls = []
    if template_ids:
        for tid in template_ids:
            tpl = resolve_template(tid)
            if tpl:
                compare_tpls.append(tpl)
    else:
        for tpl in GROUPING_TEMPLATES:
            if tier_rank.get(tpl.get("tier", "free"), 0) <= user_rank:
                compare_tpls.append(tpl)
            if len(compare_tpls) >= 4:
                break

    scenarios = []
    for tpl in compare_tpls:
        cfg = template_to_group_config(tpl["id"], {})
        try:
            result = algo.create_groups(
                profiles,
                group_size=group_size,
                mode=cfg.get("mode", "heterogeneous"),
                priority=cfg.get("priority", "skill"),
                constraints=cfg.get("constraints") or {},
            )
            scenarios.append(
                {
                    "key": tpl["id"],
                    "label": tpl["name"],
                    "template_id": tpl["id"],
                    "balance_score": result["balance_score"],
                    "skill_spread_within_groups": result.get("skill_spread_within_groups"),
                    "config": result.get("config"),
                    "groups": _enrich_groups_for_ui(result["groups"], profiles),
                }
            )
        except ValueError as e:
            scenarios.append({"key": tpl["id"], "label": tpl["name"], "error": str(e)})
    from app.models import UserSubscription

    sub = UserSubscription.query.filter_by(user_id=uid).first()
    if sub:
        sub.deep_preview_used = (sub.deep_preview_used or 0) + 1
        db.session.commit()
    write_audit("group_compare", detail=json.dumps({"count": len(scenarios)}))
    return jsonify({"scenarios": scenarios})


@bp.route("/preview", methods=["POST"])
@admin_required
def preview_groups():
    """模拟分组，不写入数据库."""
    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    group_size = int(data.get("group_size", 4))
    config = data.get("config") or {}
    template_id = config.get("template_id") or data.get("template_id")
    if template_id:
        tpl = resolve_template(template_id)
        if tpl.get("tier") == "pro":
            ent = get_entitlements(get_request_user_id())
            if ent.get("plan_code") == "free":
                return jsonify({"error": "该分组模板需升级专业版", "code": "PAYWALL", "feature": "grouping.template"}), 402
        config = template_to_group_config(template_id, config)
    mode = config.get("mode", "heterogeneous")
    priority = config.get("priority", "skill")
    constraints = config.get("constraints") or {}

    if not user_ids:
        return jsonify({"error": "user_ids 不能为空"}), 400

    profiles = []
    for uid in user_ids:
        prof = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            profiles.append(_profile_to_dict(prof))

    if len(profiles) < group_size:
        return jsonify({"error": "有效画像人数不足"}), 400

    try:
        result = algo.create_groups(
            profiles,
            group_size=group_size,
            mode=mode,
            priority=priority,
            constraints=constraints,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    major_dist = {}
    for g in result["groups"]:
        for m in g.get("members") or []:
            maj = m.get("major") or "未知"
            major_dist[maj] = major_dist.get(maj, 0) + 1

    return jsonify(
        {
            "preview": True,
            "groups": _enrich_groups_for_ui(result["groups"], profiles),
            "balance_score": result["balance_score"],
            "skill_spread_within_groups": result.get("skill_spread_within_groups"),
            "config": result["config"],
            "major_distribution": major_dist,
        }
    )


@bp.route("/list", methods=["GET"])
@jwt_required()
def list_groups():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 401
    activity_id = request.args.get("activity_id", type=int)
    q = GroupInfo.query
    if activity_id:
        q = q.filter_by(activity_id=activity_id)
    groups = q.order_by(GroupInfo.create_time.desc()).all()
    if user.role != "admin":
        groups = [g for g in groups if uid in g.member_list()]
    return jsonify([g.to_dict() for g in groups])


@bp.route("/<int:group_id>", methods=["GET"])
@jwt_required()
def get_group(group_id):
    from app.services.group_config import load_group_config, get_team_role

    uid = get_request_user_id()
    user = User.query.get(uid)
    g = GroupInfo.query.get_or_404(group_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 401
    if user.role != "admin" and uid not in g.member_list():
        return jsonify({"error": "无权访问该小组"}), 403
    cfg = load_group_config(g)
    members = []
    for mid in g.member_list():
        prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
        u = User.query.get(mid)
        members.append(
            {
                "user": u.to_dict() if u else None,
                "profile": prof.to_dict() if prof else None,
                "team_role": get_team_role(cfg, mid),
            }
        )
    data = g.to_dict()
    data["member_roles"] = cfg.get("member_roles") or []
    data["members_detail"] = members
    return jsonify(data)


@bp.route("/<int:group_id>/members", methods=["PUT"])
@admin_required
def update_members(group_id):
    g = GroupInfo.query.get_or_404(group_id)
    data = request.get_json(silent=True) or {}
    member_ids = data.get("member_ids") or []
    profiles = []
    for mid in member_ids:
        prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            profiles.append(_profile_to_dict(prof))
    validation = algo.validate_manual(profiles, len(member_ids))
    g.member_ids = json.dumps(member_ids)
    if profiles:
        g.avg_skill = sum(p.get("skill_final") or p.get("skill_score", 0) for p in profiles) / len(profiles)
    db.session.commit()
    write_audit("group_manual_adjust", "group", group_id)
    return jsonify({"group": g.to_dict(), "validation": validation})
