"""任务分配与调优 API."""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.models import BehaviorLog, GroupInfo, Task, User, UserProfile
from app.services.algorithms.task_adjust import TaskAdjustAlgorithm
from app.services.algorithms.task_assign import TaskAssignAlgorithm
from app.services.task_service import create_assigned_tasks, parse_deadline

bp = Blueprint("task", __name__)
assigner = TaskAssignAlgorithm()
adjuster = TaskAdjustAlgorithm()


def _members_profiles(group: GroupInfo) -> list:
    members = []
    for mid in group.member_list():
        prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
        if prof:
            d = prof.to_dict()
            d["user_id"] = mid
            members.append(d)
    return members


def _user_in_group(user_id: int, group_id: int | None) -> bool:
    if not group_id:
        return False
    group = GroupInfo.query.get(group_id)
    return bool(group and user_id in group.member_list())


@bp.route("/assign", methods=["POST"])
@admin_required
def assign_tasks():
    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    template_key = data.get("template_key", "product_dev")
    team_goal = data.get("team_goal", "")
    custom_tasks = data.get("custom_tasks")

    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    members = _members_profiles(group)
    if not members:
        return jsonify({"error": "组内无有效画像"}), 400

    assignments = assigner.assign(group_id, members, template_key, custom_tasks, team_goal)
    created = create_assigned_tasks(group_id, assignments)
    db.session.commit()
    write_audit("task_assign", "group", group_id)
    return jsonify({"tasks": [t.to_dict() for t in created]})


@bp.route("/list", methods=["GET"])
@jwt_required()
def list_tasks():
    uid = get_request_user_id()
    group_id = request.args.get("group_id", type=int)
    q = Task.query
    if group_id:
        q = q.filter_by(group_id=group_id)
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 401
    if user.role != "admin":
        q = q.filter((Task.assignee_id == uid) | Task.group_id.in_(
            [g.id for g in GroupInfo.query.all() if uid in g.member_list()]
        ))
    tasks = q.order_by(Task.create_time.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@bp.route("/create", methods=["POST"])
@jwt_required()
def create_task():
    """学生或教师创建一条小组任务，支持学生主动认领自己想做的工作."""
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 401

    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    if user.role != "admin" and uid not in group.member_list():
        return jsonify({"error": "只能在自己的小组内创建任务"}), 403

    task_name = (data.get("task_name") or "").strip()
    if not task_name:
        return jsonify({"error": "任务名称必填"}), 400

    assignee_id = data.get("assignee_id") or uid
    if user.role != "admin":
        assignee_id = uid
    elif assignee_id and int(assignee_id) not in group.member_list():
        return jsonify({"error": "负责人必须是小组成员"}), 400

    description = (data.get("description") or "").strip()
    reason = (data.get("reason") or "").strip()
    source_note = "【学生自建】" if user.role != "admin" else "【教师创建】"
    if reason:
        description = f"{description}\n\n【创建说明】{reason}".strip()
    description = f"{description}\n\n{source_note}".strip()

    try:
        difficulty = int(data.get("difficulty") or 3)
    except (TypeError, ValueError):
        difficulty = 3
    difficulty = max(1, min(5, difficulty))

    try:
        estimated_hours = float(data.get("estimated_hours") or 2)
    except (TypeError, ValueError):
        estimated_hours = 2
    estimated_hours = max(0.5, min(80, estimated_hours))

    task = Task(
        task_name=task_name,
        description=description,
        difficulty=difficulty,
        group_id=group.id,
        assignee_id=int(assignee_id),
        role_required=(data.get("role_required") or "").strip() or None,
        estimated_hours=estimated_hours,
        deadline=parse_deadline(data.get("deadline")),
        status="pending",
        progress=0,
        depends_on=json.dumps([]),
    )
    db.session.add(task)
    db.session.flush()
    db.session.add(
        BehaviorLog(
            user_id=uid,
            task_id=task.id,
            group_id=group.id,
            progress=0,
            submit_status="created",
            active_count=1,
            event_type="task_create",
            detail=json.dumps({"task_name": task_name, "source": source_note}, ensure_ascii=False),
        )
    )
    db.session.commit()
    write_audit("task_create", "task", task.id, json.dumps({"group_id": group.id, "creator_id": uid}, ensure_ascii=False))
    return jsonify(task.to_dict()), 201


@bp.route("/<int:task_id>/progress", methods=["POST"])
@jwt_required()
def update_progress(task_id):
    uid = get_request_user_id()
    task = Task.query.get_or_404(task_id)
    user = User.query.get(uid)
    if user.role != "admin" and task.assignee_id != uid:
        return jsonify({"error": "只能更新自己的任务进度"}), 403
    data = request.get_json(silent=True) or {}
    progress = int(data.get("progress", task.progress))
    progress = max(0, min(100, progress))
    task.progress = progress
    if progress >= 100:
        task.status = "done"
    elif progress > 0:
        task.status = "in_progress"
    status_note = data.get("submit_status", "on_time")
    db.session.add(
        BehaviorLog(
            user_id=uid,
            task_id=task_id,
            group_id=task.group_id,
            progress=progress,
            submit_status=status_note,
            active_count=1,
            event_type="progress",
            detail=data.get("detail"),
        )
    )
    db.session.commit()
    return jsonify(task.to_dict())


@bp.route("/<int:task_id>/feedback", methods=["POST"])
@jwt_required()
def submit_task_feedback(task_id):
    """学生提交任务负载/适配反馈，供一周后调优和教师督促使用."""
    uid = get_request_user_id()
    task = Task.query.get_or_404(task_id)
    user = User.query.get(uid)
    if user.role != "admin" and task.assignee_id != uid and not _user_in_group(uid, task.group_id):
        return jsonify({"error": "无权反馈该任务"}), 403
    data = request.get_json(silent=True) or {}
    feedback_type = (data.get("feedback_type") or "needs_help").strip()
    workload = data.get("workload")
    try:
        workload_score = float(workload) if workload is not None else None
    except (TypeError, ValueError):
        workload_score = None
    tendency = "negative" if feedback_type in {"too_heavy", "not_fit", "blocked", "needs_help"} else "normal"
    detail = {
        "feedback_type": feedback_type,
        "message": (data.get("message") or "").strip(),
        "expected_adjustment": (data.get("expected_adjustment") or "").strip(),
        "workload": workload_score,
    }
    log = BehaviorLog(
        user_id=uid,
        task_id=task.id,
        group_id=task.group_id,
        progress=task.progress or 0,
        submit_status="feedback",
        active_count=1,
        collab_score=workload_score,
        tendency=tendency,
        event_type="task_feedback",
        detail=json.dumps(detail, ensure_ascii=False),
    )
    db.session.add(log)
    db.session.commit()
    write_audit("task_feedback", "task", task.id, json.dumps(detail, ensure_ascii=False))
    return jsonify(log.to_dict()), 201


@bp.route("/adjust", methods=["POST"])
@admin_required
def adjust_tasks():
    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    tasks = Task.query.filter_by(group_id=group_id).all()
    logs = BehaviorLog.query.filter_by(group_id=group_id).all()
    summary = adjuster.summarize_behavior(logs)
    result = adjuster.adjust([t.to_dict() for t in tasks], summary, _members_profiles(group))

    for t in tasks:
        for sug in result["suggestions"]:
            if sug.get("task_id") == t.id:
                t.pending_adjust = json.dumps(sug, ensure_ascii=False)
    db.session.commit()
    write_audit("task_adjust", "group", group_id)
    return jsonify(result)


@bp.route("/<int:task_id>/adjust/confirm", methods=["POST"])
@admin_required
def confirm_adjust(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json(silent=True) or {}
    accept = data.get("accept", True)
    if accept and task.pending_adjust:
        sug = json.loads(task.pending_adjust)
        adjuster.apply_suggestion(task, sug)
    else:
        task.pending_adjust = None
    db.session.commit()
    return jsonify(task.to_dict())


@bp.route("/templates", methods=["GET"])
@jwt_required()
def list_templates():
    return jsonify(assigner.templates)
