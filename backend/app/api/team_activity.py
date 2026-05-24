"""组队活动 API：老师发起活动，学生参与或自由组队."""
from __future__ import annotations

import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.models import (
    ClassMembership,
    Classroom,
    GroupInfo,
    TeamActivity,
    TeamActivityParticipant,
    TeamConfirmation,
    TeamJoinRequest,
    TeamRoom,
    User,
    UserProfile,
)
from app.services.algorithms.grouping import GroupingAlgorithm
from app.services.ai_insights import activity_grouping_insight, group_ai_insight
from app.services.class_grouping import suggest_group_sizes
from app.services.group_config import load_group_config, set_member_roles
from app.services.role_assign import assign_roles_for_group
from app.services.tag_catalog import normalize_active_tags

bp = Blueprint("team_activity", __name__)
admin_bp = Blueprint("admin_team_activity", __name__)
group_algo = GroupingAlgorithm()
FREE_TEAM_EDIT_STATUSES = {"collecting", "grouping", "confirming"}


def _json(data) -> str:
    return json.dumps(data or [], ensure_ascii=False)


def _parse_dt(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _latest_profile(uid: int):
    return UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()


def _activity_counts(activity: TeamActivity) -> dict:
    return {
        "participant_count": TeamActivityParticipant.query.filter_by(activity_id=activity.id).count(),
        "team_count": TeamRoom.query.filter_by(activity_id=activity.id).count(),
        "group_count": GroupInfo.query.filter_by(activity_id=activity.id).count(),
    }


def _activity_to_dict(activity: TeamActivity, *, include_classroom: bool = True) -> dict:
    data = activity.to_dict(counts=_activity_counts(activity))
    if include_classroom and activity.class_id:
        cls = Classroom.query.get(activity.class_id)
        data["classroom"] = cls.to_dict(member_count=len(_class_member_ids(cls.id))) if cls else None
    return data


def _class_member_ids(class_id: int | None) -> list[int]:
    if not class_id:
        return []
    rows = ClassMembership.query.filter_by(class_id=class_id, status="active").all()
    return [r.user_id for r in rows]


def _ensure_activity_participant(activity: TeamActivity, user_id: int):
    participant = _participant_for(activity.id, user_id)
    prof = _latest_profile(user_id)
    if not participant:
        participant = TeamActivityParticipant(activity_id=activity.id, user_id=user_id)
        db.session.add(participant)
    participant.status = "joined"
    if prof and not participant.active_tags_json:
        participant.active_tags_json = json.dumps(normalize_active_tags(prof.to_dict().get("active_tags") or []), ensure_ascii=False)
        participant.passive_tags_json = json.dumps(prof.to_dict().get("passive_tags") or [], ensure_ascii=False)
        participant.profile_snapshot_json = json.dumps(prof.to_dict(), ensure_ascii=False)
    return participant


def _participant_for(activity_id: int, user_id: int):
    return TeamActivityParticipant.query.filter_by(activity_id=activity_id, user_id=user_id).first()


def _free_team_edit_error(activity: TeamActivity, user_id: int):
    if activity.mode != "free_team":
        return jsonify({"error": "当前活动不是自由组队模式"}), 400
    if activity.status not in FREE_TEAM_EDIT_STATUSES:
        return jsonify({"error": "当前活动已锁定，不能继续调整自由队伍"}), 400
    if not _participant_for(activity.id, user_id):
        return jsonify({"error": "请先参与该组队活动"}), 400
    return None


def _user_map(ids):
    users = User.query.filter(User.id.in_(ids)).all() if ids else []
    return {u.id: u.to_dict() for u in users}


def _room_to_dict(room: TeamRoom):
    mids = room.member_ids()
    data = room.to_dict(_user_map(mids))
    pending = TeamJoinRequest.query.filter_by(team_id=room.id, status="pending").all()
    data["pending_requests"] = [
        r.to_dict(User.query.get(r.user_id)) for r in pending
    ]
    return data


def _confirmation_for(activity_id: int, user_id: int):
    return TeamConfirmation.query.filter_by(activity_id=activity_id, user_id=user_id).order_by(TeamConfirmation.update_time.desc()).first()


def _confirmation_to_dict(conf: TeamConfirmation, users: dict | None = None):
    return conf.to_dict((users or {}).get(conf.user_id))


def _group_to_dict(group: GroupInfo, *, include_confirmations: bool = False):
    data = group.to_dict()
    users = _user_map(group.member_list())
    data["members"] = [users.get(mid) for mid in group.member_list() if users.get(mid)]
    if include_confirmations:
        confirmations = TeamConfirmation.query.filter_by(group_id=group.id).all()
        data["confirmations"] = [_confirmation_to_dict(c, users) for c in confirmations]
        total = max(len(group.member_list()), 1)
        accepted = sum(1 for c in confirmations if c.status in {"accepted", "resolved"} and c.accept_team)
        adjust = sum(1 for c in confirmations if c.status == "adjust_requested")
        data["confirmation_summary"] = {
            "accepted": accepted,
            "adjust_requested": adjust,
            "pending": max(total - len(confirmations), 0) + sum(1 for c in confirmations if c.status == "pending"),
            "total": total,
            "accept_rate": round(accepted / total * 100, 1),
        }
    return data


def _build_group_ai_analysis(group_payload: dict, member_profiles: list[dict]) -> dict:
    member_set = set(group_payload.get("member_ids") or [])
    members = [p for p in member_profiles if p.get("user_id") in member_set]
    return group_ai_insight(group_payload, members)


def _profile_for_group(uid: int, participant: TeamActivityParticipant | None = None) -> dict | None:
    prof = _latest_profile(uid)
    if not prof:
        return None
    d = prof.to_dict()
    d["user_id"] = uid
    if participant:
        active = normalize_active_tags(json.loads(participant.active_tags_json or "[]"))
        if active:
            d["active_tags"] = active
    return d


@admin_bp.route("/team-activities", methods=["GET", "POST"])
@admin_required
def admin_team_activities():
    if request.method == "GET":
        activities = TeamActivity.query.order_by(TeamActivity.create_time.desc()).all()
        return jsonify([_activity_to_dict(a) for a in activities])

    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "活动标题不能为空"}), 400
    class_id = data.get("class_id")
    if not class_id:
        return jsonify({"error": "创建组队活动必须选择班级范围"}), 400
    classroom = Classroom.query.get(class_id)
    if not classroom:
        return jsonify({"error": "班级不存在"}), 404
    activity = TeamActivity(
        title=title,
        description=(data.get("description") or "").strip(),
        course_name=(data.get("course_name") or classroom.course_name or "").strip(),
        mode=data.get("mode") or "task_auto",
        status=data.get("status") or "draft",
        group_size=int(data.get("group_size") or 4),
        task_goal=(data.get("task_goal") or "").strip(),
        required_tags_json=_json(data.get("required_tags") or []),
        required_roles_json=_json(data.get("required_roles") or []),
        deadline=_parse_dt(data.get("deadline")),
        class_id=classroom.id,
        created_by=uid,
    )
    db.session.add(activity)
    db.session.commit()
    write_audit("team_activity_create", "team_activity", activity.id)
    return jsonify(_activity_to_dict(activity)), 201


@admin_bp.route("/team-activities/<int:activity_id>", methods=["GET", "PUT"])
@admin_required
def admin_team_activity_detail(activity_id):
    activity = TeamActivity.query.get_or_404(activity_id)
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        for key in ("title", "description", "course_name", "mode", "status", "task_goal"):
            if key in data:
                setattr(activity, key, (data.get(key) or "").strip())
        if "group_size" in data:
            activity.group_size = int(data.get("group_size") or activity.group_size or 4)
        if "required_tags" in data:
            activity.required_tags_json = _json(data.get("required_tags") or [])
        if "required_roles" in data:
            activity.required_roles_json = _json(data.get("required_roles") or [])
        if "deadline" in data:
            activity.deadline = _parse_dt(data.get("deadline"))
        if "class_id" in data:
            class_id = data.get("class_id")
            if not class_id:
                return jsonify({"error": "组队活动必须归属于一个班级"}), 400
            if not Classroom.query.get(class_id):
                return jsonify({"error": "班级不存在"}), 404
            activity.class_id = class_id
        db.session.commit()
        write_audit("team_activity_update", "team_activity", activity.id)
    return jsonify(_activity_detail(activity))


@admin_bp.route("/team-activities/<int:activity_id>/publish-collect", methods=["POST"])
@admin_required
def publish_collect(activity_id):
    activity = TeamActivity.query.get_or_404(activity_id)
    activity.status = "collecting"
    db.session.commit()
    write_audit("team_activity_collecting", "team_activity", activity.id)
    return jsonify(_activity_detail(activity))


@admin_bp.route("/team-activities/<int:activity_id>/auto-group", methods=["POST"])
@admin_required
def auto_group(activity_id):
    activity = TeamActivity.query.get_or_404(activity_id)
    if activity.class_id:
        member_ids = _class_member_ids(activity.class_id)
        if len(member_ids) < 2:
            return jsonify({"error": "班级有效成员不足，无法自动分组"}), 400
        for mid in member_ids:
            _ensure_activity_participant(activity, mid)
        db.session.flush()
        participants = TeamActivityParticipant.query.filter(
            TeamActivityParticipant.activity_id == activity.id,
            TeamActivityParticipant.user_id.in_(member_ids),
        ).all()
    else:
        participants = TeamActivityParticipant.query.filter_by(activity_id=activity.id).all()
    profiles = []
    for p in participants:
        prof = _profile_for_group(p.user_id, p)
        if prof:
            profiles.append(prof)
    if len(profiles) < min(activity.group_size, 2):
        return jsonify({"error": "参与人数不足，无法自动分组"}), 400

    TeamConfirmation.query.filter_by(activity_id=activity.id).delete()
    GroupInfo.query.filter_by(activity_id=activity.id).delete()
    task_requirements = {
        "goal": activity.task_goal,
        "required_tags": activity.required_tags(),
        "required_roles": activity.required_roles(),
    }
    result = group_algo.create_groups(
        profiles,
        group_size=activity.group_size,
        mode="task_auto",
        task_requirements=task_requirements,
        target_sizes=suggest_group_sizes(len(profiles), activity.group_size) if activity.class_id and activity.group_size >= 3 else None,
    )
    saved = []
    for g in result["groups"]:
        group_payload = {
            "group_name": g["group_name"],
            "member_ids": g["member_ids"],
            "avg_knowledge": g["avg_knowledge"],
            "avg_skill": g["avg_skill"],
            "avg_collab": g["avg_collab"],
            "balance_score": result["balance_score"],
        }
        group = GroupInfo(
            activity_id=activity.id,
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
                    "ai_analysis": _build_group_ai_analysis(group_payload, profiles),
                },
                ensure_ascii=False,
            ),
        )
        db.session.add(group)
        db.session.flush()
        roles = assign_roles_for_group(g.get("members") or [])
        set_member_roles(group, roles)
        role_map = {int(r["user_id"]): r for r in roles if r.get("user_id") is not None}
        for mid in group.member_list():
            role = role_map.get(int(mid), {})
            db.session.add(
                TeamConfirmation(
                    activity_id=activity.id,
                    group_id=group.id,
                    user_id=mid,
                    status="pending",
                    preferred_role=role.get("role"),
                    message=role.get("reason"),
                )
            )
        saved.append(group)
    activity.status = "confirming"
    db.session.commit()
    group_payloads = [_group_to_dict(g, include_confirmations=True) for g in saved]
    ai_analysis = activity_grouping_insight(activity.to_dict(counts=_activity_counts(activity)), group_payloads, use_llm=False)
    write_audit("team_activity_auto_group", "team_activity", activity.id, json.dumps({"groups": len(saved)}))
    return jsonify({"activity": activity.to_dict(counts=_activity_counts(activity)), "groups": group_payloads, "ai_analysis": ai_analysis})


@admin_bp.route("/team-activities/<int:activity_id>/publish-groups", methods=["POST"])
@admin_required
def publish_groups(activity_id):
    activity = TeamActivity.query.get_or_404(activity_id)
    if not GroupInfo.query.filter_by(activity_id=activity.id).count():
        return jsonify({"error": "暂无可发布的小组"}), 400
    activity.status = "locked"
    db.session.commit()
    write_audit("team_activity_publish_groups", "team_activity", activity.id)
    return jsonify(_activity_detail(activity))


@admin_bp.route("/team-activities/<int:activity_id>/lock-groups", methods=["POST"])
@admin_required
def lock_groups(activity_id):
    """确认期结束后锁定候选小组为正式团队."""
    return publish_groups(activity_id)


@admin_bp.route("/team-activities/<int:activity_id>/confirmations/<int:confirmation_id>/resolve", methods=["POST"])
@admin_required
def resolve_confirmation(activity_id, confirmation_id):
    """处理学生的角色/任务微调申请."""
    admin_uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    conf = TeamConfirmation.query.get_or_404(confirmation_id)
    if conf.activity_id != activity.id:
        return jsonify({"error": "确认记录不属于该活动"}), 400
    data = request.get_json(silent=True) or {}
    action = data.get("status") or data.get("action") or "resolved"
    if action not in {"resolved", "rejected", "accepted"}:
        return jsonify({"error": "处理状态不支持"}), 400
    conf.status = "accepted" if action == "accepted" else action
    if action in {"resolved", "accepted"}:
        conf.accept_team = True
        conf.accept_role = True
    conf.handled_by = admin_uid
    conf.handled_note = (data.get("handled_note") or data.get("note") or "").strip()

    new_role = (data.get("preferred_role") or data.get("role") or "").strip()
    if new_role:
        conf.preferred_role = new_role
        group = GroupInfo.query.get(conf.group_id)
        if group:
            cfg = load_group_config(group)
            roles = cfg.get("member_roles") or []
            found = False
            for item in roles:
                if int(item.get("user_id", -1)) == conf.user_id:
                    item["role"] = new_role
                    item["source"] = "teacher_adjust"
                    item["reason"] = conf.handled_note or "教师根据预沟通反馈调整"
                    item["assigned_at"] = datetime.utcnow().isoformat()
                    found = True
                    break
            if not found:
                roles.append(
                    {
                        "user_id": conf.user_id,
                        "role": new_role,
                        "source": "teacher_adjust",
                        "reason": conf.handled_note or "教师根据预沟通反馈调整",
                        "assigned_at": datetime.utcnow().isoformat(),
                    }
                )
            set_member_roles(group, roles)
    db.session.commit()
    write_audit("team_confirmation_resolve", "team_activity", activity.id, json.dumps({"confirmation_id": conf.id, "status": conf.status}, ensure_ascii=False))
    return jsonify(_confirmation_to_dict(conf, _user_map([conf.user_id])))


@admin_bp.route("/team-activities/<int:activity_id>/lock-free-teams", methods=["POST"])
@admin_required
def lock_free_teams(activity_id):
    activity = TeamActivity.query.get_or_404(activity_id)
    rooms = TeamRoom.query.filter_by(activity_id=activity.id).all()
    if not rooms:
        return jsonify({"error": "暂无学生队伍可锁定"}), 400
    GroupInfo.query.filter_by(activity_id=activity.id).delete()
    saved = []
    for idx, room in enumerate(rooms, start=1):
        mids = room.member_ids()
        if not mids:
            continue
        profiles = [_profile_for_group(mid) for mid in mids]
        profiles = [p for p in profiles if p]
        avg = lambda dim: sum(float(p.get(f"{dim}_final") or p.get(f"{dim}_score") or 0) for p in profiles) / max(len(profiles), 1)
        group = GroupInfo(
            activity_id=activity.id,
            group_name=room.name or f"自由队伍{idx}",
            member_ids=json.dumps(mids),
            avg_knowledge=round(avg("knowledge"), 2),
            avg_skill=round(avg("skill"), 2),
            avg_collab=round(avg("collab"), 2),
            balance_score=8,
            config=json.dumps({"mode": "free_team", "complement_note": "学生自由组队，老师已锁定为正式队伍"}, ensure_ascii=False),
        )
        db.session.add(group)
        db.session.flush()
        set_member_roles(group, assign_roles_for_group(profiles))
        room.status = "locked"
        room.group_id = group.id
        saved.append(group)
    activity.status = "locked"
    db.session.commit()
    write_audit("team_activity_lock_free", "team_activity", activity.id)
    return jsonify({"activity": activity.to_dict(counts=_activity_counts(activity)), "groups": [g.to_dict() for g in saved]})


@bp.route("/active", methods=["GET"])
@jwt_required()
def active_activities():
    uid = get_request_user_id()
    activities = TeamActivity.query.filter(TeamActivity.status.in_(["collecting", "grouping", "preview", "confirming", "published", "locked", "tasking", "adjusting"])).order_by(TeamActivity.create_time.desc()).all()
    my_class_ids = {
        row.class_id
        for row in ClassMembership.query.filter_by(user_id=uid, status="active").all()
    }
    out = []
    for a in activities:
        if a.class_id and a.class_id not in my_class_ids:
            continue
        d = _activity_to_dict(a)
        participant = _participant_for(a.id, uid)
        d["my_participant"] = participant.to_dict() if participant else None
        my_group = _my_group(a.id, uid)
        d["my_group"] = _group_to_dict(my_group, include_confirmations=True) if my_group else None
        conf = _confirmation_for(a.id, uid)
        d["my_confirmation"] = conf.to_dict() if conf else None
        out.append(d)
    return jsonify(out)


@bp.route("/<int:activity_id>/join", methods=["POST"])
@jwt_required()
def join_activity(activity_id):
    uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    if activity.status not in {"collecting", "grouping", "confirming"}:
        return jsonify({"error": "当前活动已停止收集成员"}), 400
    if activity.class_id and uid not in _class_member_ids(activity.class_id):
        return jsonify({"error": "你不属于该活动绑定班级，无法参与"}), 403
    data = request.get_json(silent=True) or {}
    participant = _participant_for(activity.id, uid)
    prof = _latest_profile(uid)
    active_tags = data.get("active_tags")
    if active_tags is None and prof:
        active_tags = prof.to_dict().get("active_tags") or []
    passive_tags = prof.to_dict().get("passive_tags") if prof else []
    if not participant:
        participant = TeamActivityParticipant(activity_id=activity.id, user_id=uid)
        db.session.add(participant)
    participant.status = "joined"
    participant.active_tags_json = json.dumps(normalize_active_tags(active_tags or []), ensure_ascii=False)
    participant.passive_tags_json = json.dumps(passive_tags or [], ensure_ascii=False)
    participant.profile_snapshot_json = json.dumps(prof.to_dict() if prof else {}, ensure_ascii=False)
    db.session.commit()
    write_audit("team_activity_join", "team_activity", activity.id)
    return jsonify(participant.to_dict())


@bp.route("/<int:activity_id>/tags", methods=["PUT"])
@jwt_required()
def update_activity_tags(activity_id):
    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    participant = _participant_for(activity_id, uid)
    if not participant:
        return jsonify({"error": "请先参与该组队活动"}), 400
    participant.active_tags_json = json.dumps(normalize_active_tags(data.get("active_tags") or []), ensure_ascii=False)
    db.session.commit()
    return jsonify(participant.to_dict())


@bp.route("/<int:activity_id>/my-team", methods=["GET"])
@jwt_required()
def my_activity_team(activity_id):
    uid = get_request_user_id()
    group = _my_group(activity_id, uid)
    if not group:
        return jsonify({})
    return jsonify(_group_to_dict(group, include_confirmations=True))


@bp.route("/<int:activity_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_candidate_team(activity_id):
    """学生在预沟通期确认候选团队/角色，或提交微调诉求."""
    uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    if activity.status not in {"preview", "confirming", "grouping"}:
        return jsonify({"error": "当前活动不在预沟通确认期"}), 400
    group = _my_group(activity_id, uid)
    if not group:
        return jsonify({"error": "暂无你的候选小组"}), 404

    data = request.get_json(silent=True) or {}
    accept_team = bool(data.get("accept_team", True))
    accept_role = bool(data.get("accept_role", True))
    status = "accepted" if accept_team and accept_role else "adjust_requested"
    conf = TeamConfirmation.query.filter_by(activity_id=activity_id, group_id=group.id, user_id=uid).first()
    if not conf:
        conf = TeamConfirmation(activity_id=activity_id, group_id=group.id, user_id=uid)
        db.session.add(conf)
    conf.accept_team = accept_team
    conf.accept_role = accept_role
    conf.status = status
    conf.preferred_role = (data.get("preferred_role") or conf.preferred_role or "").strip()
    prefs = data.get("task_preferences") or []
    if isinstance(prefs, str):
        prefs = [p.strip() for p in prefs.split("、") if p.strip()]
    conf.task_preferences_json = json.dumps(prefs, ensure_ascii=False)
    conf.reason = (data.get("reason") or "").strip()
    conf.message = (data.get("message") or "").strip()
    db.session.commit()
    write_audit("team_confirmation_submit", "team_activity", activity.id, json.dumps({"group_id": group.id, "status": status}, ensure_ascii=False))
    return jsonify(_confirmation_to_dict(conf, _user_map([uid])))


@bp.route("/<int:activity_id>/confirmations", methods=["GET"])
@jwt_required()
def my_confirmations(activity_id):
    uid = get_request_user_id()
    group = _my_group(activity_id, uid)
    if not group:
        return jsonify([])
    users = _user_map(group.member_list())
    confirmations = TeamConfirmation.query.filter_by(group_id=group.id).all()
    return jsonify([_confirmation_to_dict(c, users) for c in confirmations])


@bp.route("/<int:activity_id>/teams", methods=["GET", "POST"])
@jwt_required()
def activity_teams(activity_id):
    uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    if request.method == "GET":
        rooms = TeamRoom.query.filter_by(activity_id=activity.id).order_by(TeamRoom.create_time.desc()).all()
        return jsonify([_room_to_dict(r) for r in rooms])
    edit_error = _free_team_edit_error(activity, uid)
    if edit_error:
        return edit_error
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip() or "我的队伍"
    if _room_for_user(activity.id, uid):
        return jsonify({"error": "你已在一个队伍中"}), 400
    room = TeamRoom(
        activity_id=activity.id,
        name=name,
        description=(data.get("description") or "").strip(),
        leader_id=uid,
        desired_tags_json=json.dumps(data.get("desired_tags") or [], ensure_ascii=False),
    )
    room.set_member_ids([uid])
    db.session.add(room)
    db.session.commit()
    return jsonify(_room_to_dict(room)), 201


@bp.route("/<int:activity_id>/teams/<int:team_id>/join-request", methods=["POST"])
@jwt_required()
def request_join_team(activity_id, team_id):
    uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    edit_error = _free_team_edit_error(activity, uid)
    if edit_error:
        return edit_error
    room = TeamRoom.query.get_or_404(team_id)
    if room.activity_id != activity_id:
        return jsonify({"error": "队伍不属于该活动"}), 400
    if uid in room.member_ids():
        return jsonify({"error": "你已在该队伍中"}), 400
    if _room_for_user(activity_id, uid):
        return jsonify({"error": "你已在其他队伍中"}), 400
    req = TeamJoinRequest.query.filter_by(activity_id=activity_id, team_id=team_id, user_id=uid, status="pending").first()
    if not req:
        data = request.get_json(silent=True) or {}
        req = TeamJoinRequest(activity_id=activity_id, team_id=team_id, user_id=uid, message=data.get("message"))
        db.session.add(req)
        db.session.commit()
    return jsonify(req.to_dict(User.query.get(uid)))


@bp.route("/<int:activity_id>/requests/<int:request_id>/<action>", methods=["POST"])
@jwt_required()
def handle_join_request(activity_id, request_id, action):
    uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    edit_error = _free_team_edit_error(activity, uid)
    if edit_error:
        return edit_error
    req = TeamJoinRequest.query.get_or_404(request_id)
    room = TeamRoom.query.get_or_404(req.team_id)
    if room.activity_id != activity_id or room.leader_id != uid:
        return jsonify({"error": "无权处理该申请"}), 403
    if action not in {"approve", "reject"}:
        return jsonify({"error": "操作不支持"}), 400
    if action == "approve":
        mids = room.member_ids()
        if req.user_id not in mids:
            mids.append(req.user_id)
            room.set_member_ids(mids)
        req.status = "approved"
    else:
        req.status = "rejected"
    db.session.commit()
    return jsonify(_room_to_dict(room))


@bp.route("/<int:activity_id>/teams/<int:team_id>/leave", methods=["POST"])
@jwt_required()
def leave_team(activity_id, team_id):
    uid = get_request_user_id()
    activity = TeamActivity.query.get_or_404(activity_id)
    edit_error = _free_team_edit_error(activity, uid)
    if edit_error:
        return edit_error
    room = TeamRoom.query.get_or_404(team_id)
    if room.activity_id != activity_id:
        return jsonify({"error": "队伍不属于该活动"}), 400
    mids = [mid for mid in room.member_ids() if mid != uid]
    if room.leader_id == uid and mids:
        room.leader_id = mids[0]
    room.set_member_ids(mids)
    if not mids:
        db.session.delete(room)
    db.session.commit()
    return jsonify({"ok": True})


def _activity_detail(activity: TeamActivity):
    participants = TeamActivityParticipant.query.filter_by(activity_id=activity.id).all()
    users = _user_map([p.user_id for p in participants])
    rooms = TeamRoom.query.filter_by(activity_id=activity.id).all()
    groups = GroupInfo.query.filter_by(activity_id=activity.id).all()
    confirmations = TeamConfirmation.query.filter_by(activity_id=activity.id).all()
    data = activity.to_dict(counts=_activity_counts(activity))
    cls = Classroom.query.get(activity.class_id) if activity.class_id else None
    data["classroom"] = cls.to_dict(member_count=len(_class_member_ids(cls.id))) if cls else None
    data["participants"] = [{**p.to_dict(), "user": users.get(p.user_id)} for p in participants]
    data["rooms"] = [_room_to_dict(r) for r in rooms]
    data["groups"] = [_group_to_dict(g, include_confirmations=True) for g in groups]
    if data["groups"]:
        data["ai_analysis"] = activity_grouping_insight(data, data["groups"], use_llm=False)
    data["confirmations"] = [_confirmation_to_dict(c, users) for c in confirmations]
    total = max(len(confirmations), 1)
    accepted = sum(1 for c in confirmations if c.status in {"accepted", "resolved"} and c.accept_team)
    data["confirmation_summary"] = {
        "accepted": accepted,
        "adjust_requested": sum(1 for c in confirmations if c.status == "adjust_requested"),
        "pending": sum(1 for c in confirmations if c.status == "pending"),
        "total": len(confirmations),
        "accept_rate": round(accepted / total * 100, 1),
    }
    return data


def _my_group(activity_id: int, uid: int):
    groups = GroupInfo.query.filter_by(activity_id=activity_id).order_by(GroupInfo.create_time.desc()).all()
    return next((g for g in groups if uid in g.member_list()), None)


def _room_for_user(activity_id: int, uid: int):
    rooms = TeamRoom.query.filter_by(activity_id=activity_id).all()
    return next((r for r in rooms if uid in r.member_ids()), None)
