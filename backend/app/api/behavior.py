"""行为埋点 API."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import BehaviorLog, GroupInfo, Task, User
from app.middleware.auth import get_request_user_id

bp = Blueprint("behavior", __name__)


@bp.route("/log", methods=["POST"])
@jwt_required()
def log_behavior():
    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 401

    task_id = data.get("task_id")
    group_id = data.get("group_id")
    task = Task.query.get(task_id) if task_id else None
    if task_id and not task:
        return jsonify({"error": "任务不存在"}), 404
    if task:
        group_id = task.group_id

    group = GroupInfo.query.get(group_id) if group_id else None
    if group_id and not group:
        return jsonify({"error": "小组不存在"}), 404
    if user.role != "admin":
        if task and task.assignee_id != uid and (not group or uid not in group.member_list()):
            return jsonify({"error": "无权记录该任务行为"}), 403
        if group and uid not in group.member_list():
            return jsonify({"error": "无权记录该小组行为"}), 403

    try:
        progress = int(data.get("progress", 0))
    except (TypeError, ValueError):
        progress = 0
    progress = max(0, min(100, progress))
    log = BehaviorLog(
        user_id=uid,
        task_id=task_id,
        group_id=group_id,
        progress=progress,
        submit_status=data.get("submit_status"),
        active_count=data.get("active_count", 1),
        collab_score=data.get("collab_score"),
        comment_count=data.get("comment_count", 0),
        peer_rating=data.get("peer_rating"),
        tendency=data.get("tendency"),
        event_type=data.get("event_type", "manual"),
        detail=data.get("detail"),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify(log.to_dict()), 201
