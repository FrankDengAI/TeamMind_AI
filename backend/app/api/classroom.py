"""班级管理、成员与加入/退出审批 API."""
from __future__ import annotations

import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.models import ClassMembership, ClassRequest, Classroom, GroupInfo, TeamActivity, TeamActivityParticipant, TeamRoom, User, UserProfile
from app.services.class_grouping import build_grouping_advice

bp = Blueprint("classroom", __name__)
admin_bp = Blueprint("admin_classroom", __name__)

ACTIVE_MEMBER = "active"
PENDING_STATUSES = {"pending_join", "pending_leave"}


def _user_map(ids):
    users = User.query.filter(User.id.in_(ids)).all() if ids else []
    return {u.id: u for u in users}


def _active_members(class_id: int):
    return ClassMembership.query.filter_by(class_id=class_id, status=ACTIVE_MEMBER).order_by(ClassMembership.create_time.asc()).all()


def _pending_count(class_id: int) -> int:
    return ClassRequest.query.filter_by(class_id=class_id, status="pending").count()


def _membership_for(class_id: int, user_id: int):
    return ClassMembership.query.filter_by(class_id=class_id, user_id=user_id).order_by(ClassMembership.update_time.desc()).first()


def _request_for(class_id: int, request_id: int):
    req = ClassRequest.query.get_or_404(request_id)
    if req.class_id != class_id:
        return None
    return req


def _class_brief(cls: Classroom, *, include_advice: bool = True):
    members = _active_members(cls.id)
    teacher = User.query.get(cls.teacher_id) if cls.teacher_id else None
    advice = build_grouping_advice(len(members), 4, use_llm=False) if include_advice else None
    data = cls.to_dict(member_count=len(members), pending_count=_pending_count(cls.id), teacher=teacher, advice=advice)
    data["activity_count"] = TeamActivity.query.filter_by(class_id=cls.id).count()
    return data


def _class_detail(cls: Classroom):
    members = _active_members(cls.id)
    users = _user_map([m.user_id for m in members])
    rows = []
    for member in members:
        prof = UserProfile.query.filter_by(user_id=member.user_id).order_by(UserProfile.create_time.desc()).first()
        rows.append(
            {
                "membership": member.to_dict(users.get(member.user_id)),
                "user": users.get(member.user_id).to_dict() if users.get(member.user_id) else None,
                "profile": prof.to_dict() if prof else None,
            }
        )
    requests = ClassRequest.query.filter_by(class_id=cls.id).order_by(ClassRequest.create_time.desc()).limit(100).all()
    req_users = _user_map([r.user_id for r in requests])
    data = _class_brief(cls)
    data["members"] = rows
    class_snapshot = cls.to_dict(member_count=len(members), pending_count=_pending_count(cls.id))
    data["requests"] = [r.to_dict(req_users.get(r.user_id), class_snapshot) for r in requests]
    data["activities"] = [
        _activity_brief(a)
        for a in TeamActivity.query.filter_by(class_id=cls.id).order_by(TeamActivity.create_time.desc()).all()
    ]
    return data


def _activity_brief(activity: TeamActivity):
    return activity.to_dict(
        counts={
            "participant_count": TeamActivityParticipant.query.filter_by(activity_id=activity.id).count(),
            "team_count": TeamRoom.query.filter_by(activity_id=activity.id).count(),
            "group_count": GroupInfo.query.filter_by(activity_id=activity.id).count(),
        }
    )


def _active_membership_or_error(class_id: int, user_id: int):
    membership = _membership_for(class_id, user_id)
    if not membership or membership.status != ACTIVE_MEMBER:
        return None, (jsonify({"error": "你不是该班级成员，不能操作该班级活动"}), 403)
    return membership, None


@admin_bp.route("/classes", methods=["GET", "POST"])
@admin_required
def admin_classes():
    uid = get_request_user_id()
    if request.method == "GET":
        classes = Classroom.query.order_by(Classroom.create_time.desc()).all()
        return jsonify([_class_brief(c) for c in classes])

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "班级名称必填"}), 400
    code = (data.get("code") or "").strip() or None
    if code and Classroom.query.filter_by(code=code).first():
        return jsonify({"error": "班级代码已存在"}), 400
    cls = Classroom(
        name=name,
        code=code,
        major=(data.get("major") or "").strip(),
        grade=(data.get("grade") or "").strip(),
        course_name=(data.get("course_name") or "").strip(),
        teacher_id=uid,
        max_students=int(data.get("max_students") or 20),
        status=data.get("status") or "active",
        description=(data.get("description") or "").strip(),
    )
    db.session.add(cls)
    db.session.commit()
    write_audit("class_create", "classroom", cls.id)
    return jsonify(_class_detail(cls)), 201


@admin_bp.route("/classes/<int:class_id>", methods=["GET", "PUT", "DELETE"])
@admin_required
def admin_class_detail(class_id):
    cls = Classroom.query.get_or_404(class_id)
    if request.method == "GET":
        return jsonify(_class_detail(cls))
    if request.method == "DELETE":
        active_activity = TeamActivity.query.filter(
            TeamActivity.class_id == cls.id,
            TeamActivity.status.in_(["collecting", "grouping", "preview", "confirming", "published", "locked", "tasking", "adjusting"]),
        ).first()
        cls.status = "archived" if active_activity else "dissolved"
        db.session.commit()
        write_audit("class_archive", "classroom", cls.id, json.dumps({"status": cls.status}, ensure_ascii=False))
        return jsonify(_class_detail(cls))

    data = request.get_json(silent=True) or {}
    for key in ("name", "code", "major", "grade", "course_name", "status", "description"):
        if key in data:
            setattr(cls, key, (data.get(key) or "").strip())
    if "max_students" in data:
        cls.max_students = int(data.get("max_students") or cls.max_students or 20)
    db.session.commit()
    write_audit("class_update", "classroom", cls.id)
    return jsonify(_class_detail(cls))


@admin_bp.route("/classes/<int:class_id>/members", methods=["POST"])
@admin_required
def add_class_members(class_id):
    cls = Classroom.query.get_or_404(class_id)
    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    if data.get("user_id"):
        user_ids.append(data.get("user_id"))
    added = []
    for raw_uid in dict.fromkeys(user_ids):
        user = User.query.get(int(raw_uid))
        if not user or user.role != "user":
            continue
        membership = _membership_for(cls.id, user.id)
        if not membership:
            membership = ClassMembership(class_id=cls.id, user_id=user.id)
            db.session.add(membership)
        membership.status = ACTIVE_MEMBER
        membership.source = "teacher_add"
        membership.joined_at = membership.joined_at or datetime.utcnow()
        membership.left_at = None
        added.append(user.id)
    db.session.commit()
    write_audit("class_members_add", "classroom", cls.id, json.dumps({"user_ids": added}, ensure_ascii=False))
    return jsonify(_class_detail(cls))


@admin_bp.route("/classes/<int:class_id>/members/<int:user_id>", methods=["DELETE"])
@admin_required
def remove_class_member(class_id, user_id):
    cls = Classroom.query.get_or_404(class_id)
    membership = _membership_for(cls.id, user_id)
    if not membership or membership.status != ACTIVE_MEMBER:
        return jsonify({"error": "该学生不在班级中"}), 404
    membership.status = "removed"
    membership.left_at = datetime.utcnow()
    membership.source = "teacher_remove"
    db.session.commit()
    write_audit("class_member_remove", "classroom", cls.id, json.dumps({"user_id": user_id}, ensure_ascii=False))
    return jsonify(_class_detail(cls))


@admin_bp.route("/classes/<int:class_id>/requests", methods=["GET"])
@admin_required
def admin_class_requests(class_id):
    Classroom.query.get_or_404(class_id)
    rows = ClassRequest.query.filter_by(class_id=class_id).order_by(ClassRequest.create_time.desc()).all()
    users = _user_map([r.user_id for r in rows])
    return jsonify([r.to_dict(users.get(r.user_id)) for r in rows])


@admin_bp.route("/classes/<int:class_id>/requests/<int:request_id>/<action>", methods=["POST"])
@admin_required
def review_class_request(class_id, request_id, action):
    if action not in {"approve", "reject"}:
        return jsonify({"error": "审批动作不支持"}), 400
    cls = Classroom.query.get_or_404(class_id)
    req = _request_for(class_id, request_id)
    if not req:
        return jsonify({"error": "申请不属于该班级"}), 400
    if req.status != "pending":
        return jsonify({"error": "申请已处理"}), 400
    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    membership = _membership_for(class_id, req.user_id)
    if action == "approve":
        if not membership:
            membership = ClassMembership(class_id=class_id, user_id=req.user_id)
            db.session.add(membership)
        if req.request_type == "join":
            membership.status = ACTIVE_MEMBER
            membership.joined_at = membership.joined_at or datetime.utcnow()
            membership.left_at = None
        else:
            membership.status = "left"
            membership.left_at = datetime.utcnow()
        req.status = "approved"
    else:
        req.status = "rejected"
        if membership and membership.status in PENDING_STATUSES:
            membership.status = ACTIVE_MEMBER if req.request_type == "leave" else "rejected"
    if membership:
        membership.request_id = req.id
    req.reviewed_by = uid
    req.reviewed_note = (data.get("note") or data.get("reviewed_note") or "").strip()
    req.reviewed_at = datetime.utcnow()
    db.session.commit()
    write_audit("class_request_review", "classroom", cls.id, json.dumps({"request_id": req.id, "action": action}, ensure_ascii=False))
    return jsonify(_class_detail(cls))


@admin_bp.route("/classes/<int:class_id>/grouping-advice", methods=["GET"])
@admin_required
def admin_class_grouping_advice(class_id):
    Classroom.query.get_or_404(class_id)
    preferred = request.args.get("group_size", default=4, type=int)
    use_llm = request.args.get("deep", default=0, type=int) == 1
    members = _active_members(class_id)
    return jsonify(build_grouping_advice(len(members), preferred, use_llm=use_llm))


@bp.route("/classes", methods=["GET"])
@jwt_required()
def list_classes():
    uid = get_request_user_id()
    classes = Classroom.query.filter_by(status="active").order_by(Classroom.create_time.desc()).all()
    pending = {
        r.class_id: r
        for r in ClassRequest.query.filter_by(user_id=uid, status="pending").order_by(ClassRequest.create_time.desc()).all()
    }
    out = []
    for cls in classes:
        item = _class_brief(cls)
        membership = _membership_for(cls.id, uid)
        item["my_membership"] = membership.to_dict() if membership else None
        item["my_pending_request"] = pending.get(cls.id).to_dict() if pending.get(cls.id) else None
        out.append(item)
    return jsonify(out)


@bp.route("/classes/my", methods=["GET"])
@jwt_required()
def my_classes():
    uid = get_request_user_id()
    memberships = ClassMembership.query.filter(
        ClassMembership.user_id == uid,
        ClassMembership.status.in_(["active", "pending_join", "pending_leave"]),
    ).order_by(ClassMembership.update_time.desc()).all()
    classes = {c.id: c for c in Classroom.query.filter(Classroom.id.in_([m.class_id for m in memberships])).all()} if memberships else {}
    requests = ClassRequest.query.filter_by(user_id=uid).order_by(ClassRequest.create_time.desc()).limit(50).all()
    return jsonify(
        {
            "memberships": [m.to_dict(classroom=classes.get(m.class_id)) for m in memberships],
            "requests": [r.to_dict(classroom=classes.get(r.class_id)) for r in requests],
        }
    )


@bp.route("/classes/<int:class_id>/activities", methods=["GET", "POST"])
@jwt_required()
def class_activities(class_id):
    uid = get_request_user_id()
    cls = Classroom.query.get_or_404(class_id)
    user = User.query.get(uid)
    is_admin = bool(user and user.role == "admin")
    if not is_admin:
        _, err = _active_membership_or_error(class_id, uid)
        if err:
            return err
    if request.method == "GET":
        rows = TeamActivity.query.filter_by(class_id=class_id).order_by(TeamActivity.create_time.desc()).all()
        if not is_admin:
            rows = [a for a in rows if a.status in {"collecting", "grouping", "preview", "confirming", "published", "locked", "tasking", "adjusting"}]
        return jsonify([_activity_brief(a) for a in rows])

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "活动标题不能为空"}), 400
    mode = data.get("mode") or "free_team"
    if mode not in {"free_team", "task_auto"}:
        return jsonify({"error": "组队方式不支持"}), 400
    activity = TeamActivity(
        title=title,
        description=(data.get("description") or "").strip(),
        course_name=(data.get("course_name") or cls.course_name or "").strip(),
        mode=mode,
        status="collecting",
        group_size=max(2, min(8, int(data.get("group_size") or 4))),
        task_goal=(data.get("task_goal") or "").strip(),
        required_tags_json=json.dumps(data.get("required_tags") or [], ensure_ascii=False),
        required_roles_json=json.dumps(data.get("required_roles") or [], ensure_ascii=False),
        class_id=cls.id,
        created_by=uid,
    )
    db.session.add(activity)
    db.session.commit()
    write_audit("student_class_activity_create", "team_activity", activity.id, json.dumps({"class_id": cls.id}, ensure_ascii=False))
    return jsonify(_activity_brief(activity)), 201


@bp.route("/classes/<int:class_id>/join-request", methods=["POST"])
@jwt_required()
def join_class_request(class_id):
    uid = get_request_user_id()
    cls = Classroom.query.get_or_404(class_id)
    if cls.status != "active":
        return jsonify({"error": "班级当前不可申请加入"}), 400
    membership = _membership_for(class_id, uid)
    if membership and membership.status == ACTIVE_MEMBER:
        return jsonify({"error": "你已在该班级中"}), 400
    if membership and membership.status == "pending_join":
        return jsonify({"error": "加入申请已提交，请等待老师审批"}), 400
    if ClassRequest.query.filter_by(class_id=class_id, user_id=uid, request_type="join", status="pending").first():
        return jsonify({"error": "加入申请已提交，请等待老师审批"}), 400
    data = request.get_json(silent=True) or {}
    req = ClassRequest(
        class_id=class_id,
        user_id=uid,
        request_type="join",
        status="pending",
        message=(data.get("message") or "").strip(),
    )
    db.session.add(req)
    db.session.flush()
    if not membership:
        membership = ClassMembership(class_id=class_id, user_id=uid)
        db.session.add(membership)
    membership.status = "pending_join"
    membership.source = "student_request"
    membership.request_id = req.id
    db.session.commit()
    write_audit("class_join_request", "classroom", cls.id)
    return jsonify(req.to_dict()), 201


@bp.route("/classes/<int:class_id>/leave-request", methods=["POST"])
@jwt_required()
def leave_class_request(class_id):
    uid = get_request_user_id()
    cls = Classroom.query.get_or_404(class_id)
    membership = _membership_for(class_id, uid)
    if not membership or membership.status != ACTIVE_MEMBER:
        return jsonify({"error": "你不在该班级中"}), 400
    if ClassRequest.query.filter_by(class_id=class_id, user_id=uid, request_type="leave", status="pending").first():
        return jsonify({"error": "退出申请已提交，请等待老师审批"}), 400
    data = request.get_json(silent=True) or {}
    req = ClassRequest(
        class_id=class_id,
        user_id=uid,
        request_type="leave",
        status="pending",
        message=(data.get("message") or "").strip(),
    )
    db.session.add(req)
    db.session.flush()
    membership.status = "pending_leave"
    membership.request_id = req.id
    db.session.commit()
    write_audit("class_leave_request", "classroom", cls.id)
    return jsonify(req.to_dict()), 201
