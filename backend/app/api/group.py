"""分组 API."""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.models import GroupInfo, User, UserProfile
from app.services.algorithms.grouping import GroupingAlgorithm

bp = Blueprint("group", __name__)
algo = GroupingAlgorithm()


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
    mode = config.get("mode", "heterogeneous")

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
        result = algo.create_groups(profiles, group_size=group_size, mode=mode)
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
