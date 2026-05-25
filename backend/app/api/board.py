"""?????? API."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.middleware.auth import jwt_required_compat

from app.models import BehaviorLog, GroupInfo, Task, TeamConfirmation, TeamReport, User, UserProfile
from app.services.analytics_service import assess_task_risk, build_group_dashboard
from app.middleware.auth import get_request_user_id

bp = Blueprint("board", __name__)


def _confirmation_summary(group_id: int) -> dict | None:
    confirmations = TeamConfirmation.query.filter_by(group_id=group_id).all()
    if not confirmations:
        return None
    accepted = sum(1 for c in confirmations if c.status in {"accepted", "resolved"} and c.accept_team)
    return {
        "accepted": accepted,
        "adjust_requested": sum(1 for c in confirmations if c.status == "adjust_requested"),
        "pending": sum(1 for c in confirmations if c.status == "pending"),
        "total": len(confirmations),
        "accept_rate": round(accepted / max(len(confirmations), 1) * 100, 1),
    }


def _build_members_board(group: GroupInfo) -> list:
    from app.services.group_config import load_group_config, get_team_role

    tasks = Task.query.filter_by(group_id=group.id).all()
    task_dicts = [t.to_dict() for t in tasks]
    cfg = load_group_config(group)
    mids = [int(x) for x in group.member_list()]
    users_map = {u.id: u for u in User.query.filter(User.id.in_(mids)).all()} if mids else {}
    profiles_map = {}
    if mids:
        for prof in UserProfile.query.filter(UserProfile.user_id.in_(mids)).order_by(
            UserProfile.user_id.asc(), UserProfile.create_time.desc()
        ).all():
            if prof.user_id not in profiles_map:
                profiles_map[prof.user_id] = prof
    logs_by_user: dict[int, list] = {mid: [] for mid in mids}
    if mids:
        for log in BehaviorLog.query.filter(
            BehaviorLog.group_id == group.id, BehaviorLog.user_id.in_(mids)
        ).all():
            logs_by_user.setdefault(log.user_id, []).append(log)
    members = []
    for mid in mids:
        u = users_map.get(mid)
        prof = profiles_map.get(mid)
        logs = logs_by_user.get(mid, [])
        members.append(
            {
                "user": u.to_dict() if u else None,
                "profile": prof.to_dict() if prof else None,
                "team_role": get_team_role(cfg, mid),
                "tasks": [t for t in task_dicts if t.get("assignee_id") == mid],
                "behavior_count": len(logs),
            }
        )
    return members, task_dicts


@bp.route("/sync", methods=["GET"])
@jwt_required_compat
def sync_board():
    uid = get_request_user_id()
    group_id = request.args.get("group_id", type=int)
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "?????"}), 401

    if group_id:
        group = GroupInfo.query.get_or_404(group_id)
        if user.role != "admin" and uid not in group.member_list():
            return jsonify({"error": "???????"}), 403
        groups = [group]
    else:
        groups = GroupInfo.query.all()
        if user.role != "admin":
            groups = [g for g in groups if uid in g.member_list()]

    result = []
    for g in groups:
        members, task_dicts = _build_members_board(g)
        logs = BehaviorLog.query.filter_by(group_id=g.id).all()
        dash = build_group_dashboard(g.to_dict(), task_dicts, members, logs)
        confirm_summary = _confirmation_summary(g.id)
        report = TeamReport.query.filter_by(group_id=g.id).order_by(TeamReport.create_time.desc()).first()
        result.append(
            {
                "group": g.to_dict(),
                "members": dash["members"],
                "tasks": dash["tasks"],
                "completion_rate": dash["summary"]["completion_rate"],
                "summary": dash["summary"],
                "alerts": dash["alerts"],
                "confirmation_summary": confirm_summary,
                "latest_report": report.to_dict() if report else None,
            }
        )

    return jsonify({"boards": result, "synced_at": __import__("datetime").datetime.utcnow().isoformat()})


@bp.route("/team/<int:group_id>/dashboard", methods=["GET"])
@jwt_required_compat
def team_dashboard(group_id):
    """??????????????????."""
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "?????"}), 401
    group = GroupInfo.query.get_or_404(group_id)
    if user.role != "admin" and uid not in group.member_list():
        return jsonify({"error": "???????"}), 403

    members, task_dicts = _build_members_board(group)
    logs = BehaviorLog.query.filter_by(group_id=group_id).all()
    dash = build_group_dashboard(group.to_dict(), task_dicts, members, logs)
    dash["confirmation_summary"] = _confirmation_summary(group.id)
    report = TeamReport.query.filter_by(group_id=group_id).order_by(TeamReport.create_time.desc()).first()
    dash["latest_report"] = report.to_dict() if report else None
    return jsonify(dash)


@bp.route("/personal", methods=["GET"])
@jwt_required_compat
def personal_stats():
    uid = get_request_user_id()
    tasks = Task.query.filter_by(assignee_id=uid).all()
    my_groups = sorted(
        [g for g in GroupInfo.query.all() if uid in g.member_list()],
        key=lambda g: (g.activity_id is not None, g.create_time),
        reverse=True,
    )
    group_ids = [g.id for g in my_groups]
    team_tasks = Task.query.filter(Task.group_id.in_(group_ids)).order_by(Task.create_time.desc()).all() if group_ids else []
    logs = BehaviorLog.query.filter_by(user_id=uid).all()
    prof = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()
    done = sum(1 for t in tasks if t.status == "done" or (t.progress or 0) >= 100)
    on_time = sum(1 for l in logs if l.submit_status == "on_time")
    feedback_count = sum(1 for l in logs if l.event_type == "task_feedback")
    task_list = []
    my_alerts = []
    for t in tasks:
        td = t.to_dict()
        risk = assess_task_risk(td)
        td["risk"] = risk
        task_list.append(td)
        if risk["level"] in ("critical", "warning"):
            my_alerts.append(
                {
                    "task_id": t.id,
                    "task_name": t.task_name,
                    "level": risk["level"],
                    "message": risk["message"],
                }
            )

    return jsonify(
        {
            "profile": prof.to_dict() if prof else None,
            "tasks": task_list,
            "team_tasks": [t.to_dict() for t in team_tasks],
            "groups": [g.to_dict() for g in my_groups],
            "alerts": my_alerts,
            "stats": {
                "completion_rate": round(done / max(len(tasks), 1) * 100, 1),
                "on_time_rate": round(on_time / max(len(logs), 1) * 100, 1),
                "active_days": len(set(l.record_time.date() for l in logs if l.record_time)),
                "task_count": len(tasks),
                "risk_count": len(my_alerts),
                "feedback_count": feedback_count,
            },
        }
    )
