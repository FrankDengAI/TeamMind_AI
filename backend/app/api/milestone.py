"""??? API."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import admin_required, get_request_user_id, jwt_required_compat, write_audit
from app.models import Classroom, ClassMembership, Milestone, TeamActivity, User
from app.services.teacher_scope import admin_owns_class

bp = Blueprint("milestone", __name__)


def _can_access_activity_milestones(activity: TeamActivity, uid: int) -> bool:
    user = User.query.get(uid)
    if not user:
        return False
    if user.role == "admin":
        if not activity.class_id:
            return True
        cls = Classroom.query.get(activity.class_id)
        return admin_owns_class(cls, uid)
    if not activity.class_id:
        return False
    m = ClassMembership.query.filter_by(
        class_id=activity.class_id, user_id=uid, status="active"
    ).first()
    return m is not None


@bp.route("/activity/<int:activity_id>", methods=["GET", "POST"])
@jwt_required_compat
def activity_milestones(activity_id):
    activity = TeamActivity.query.get_or_404(activity_id)
    uid = get_request_user_id()
    group_id = request.args.get("group_id", type=int)
    if request.method == "GET":
        if not _can_access_activity_milestones(activity, uid):
            return jsonify({"error": "????"}), 403
        q = Milestone.query.filter_by(activity_id=activity_id)
        if group_id:
            q = q.filter((Milestone.group_id == group_id) | (Milestone.group_id.is_(None)))
        rows = q.order_by(Milestone.sort_order.asc(), Milestone.id.asc()).all()
        return jsonify([m.to_dict() for m in rows])
    user = User.query.get(get_request_user_id())
    if not user or user.role != "admin":
        return jsonify({"error": "?????????"}), 403
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title ??"}), 400
    due_raw = data.get("due_at")
    due_at = None
    if due_raw:
        try:
            due_at = datetime.fromisoformat(str(due_raw).replace("Z", ""))
        except ValueError:
            pass
    row = Milestone(
        activity_id=activity_id,
        group_id=data.get("group_id"),
        title=title,
        due_at=due_at,
        status=data.get("status") or "pending",
        sort_order=int(data.get("sort_order") or 0),
    )
    db.session.add(row)
    db.session.commit()
    write_audit("milestone_create", "team_activity", activity_id)
    return jsonify(row.to_dict()), 201


@bp.route("/<int:milestone_id>", methods=["PUT"])
@admin_required
def update_milestone(milestone_id):
    row = Milestone.query.get_or_404(milestone_id)
    data = request.get_json(silent=True) or {}
    if "title" in data:
        row.title = (data.get("title") or row.title).strip()
    if "status" in data:
        row.status = data.get("status")
    if "due_at" in data and data.get("due_at"):
        try:
            row.due_at = datetime.fromisoformat(str(data["due_at"]).replace("Z", ""))
        except ValueError:
            pass
    db.session.commit()
    return jsonify(row.to_dict())
