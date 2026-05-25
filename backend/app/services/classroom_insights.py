"""班级健康度、催办名单与学期时间轴."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from app.models import (
    ClassMembership,
    Classroom,
    GroupInfo,
    Task,
    TeamActivity,
    TeamActivityParticipant,
    TeamConfirmation,
    User,
    UserProfile,
)

ACTIVE = "active"


def default_timeline(course_name: str | None = None) -> list[dict[str, Any]]:
    label = course_name or "课程"
    return [
        {"key": "profile", "title": "画像采集", "hint": "学生完成标签与自述", "offset_days": 0, "status": "pending"},
        {"key": "grouping", "title": "组队确认", "hint": "发布活动并完成预沟通", "offset_days": 7, "status": "pending"},
        {"key": "midterm", "title": "中期检查", "hint": "查看任务进度与风险", "offset_days": 21, "status": "pending"},
        {"key": "final", "title": "期末展示", "hint": "导出过程评价与团队报告", "offset_days": 42, "status": "pending"},
    ]


def load_timeline(cls: Classroom) -> list[dict[str, Any]]:
    raw = getattr(cls, "timeline_json", None) or ""
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data
        except (TypeError, json.JSONDecodeError):
            pass
    return default_timeline(cls.course_name)


def save_timeline(cls: Classroom, items: list[dict]) -> list[dict]:
    cls.timeline_json = json.dumps(items, ensure_ascii=False)
    return items


def _active_member_ids(class_id: int) -> list[int]:
    rows = ClassMembership.query.filter_by(class_id=class_id, status=ACTIVE).all()
    return [r.user_id for r in rows]


def build_class_health(class_id: int) -> dict[str, Any]:
    cls = Classroom.query.get(class_id)
    if not cls:
        raise ValueError("班级不存在")
    member_ids = _active_member_ids(class_id)
    total = len(member_ids)
    with_profile = 0
    if member_ids:
        for uid in member_ids:
            if UserProfile.query.filter_by(user_id=uid).first():
                with_profile += 1
    profile_rate = round(with_profile / max(total, 1) * 100, 1)

    activities = TeamActivity.query.filter_by(class_id=class_id).all()
    active_statuses = {"collecting", "grouping", "preview", "confirming", "published", "tasking", "adjusting"}
    active_acts = [a for a in activities if a.status in active_statuses]
    participants = 0
    for act in activities:
        participants += TeamActivityParticipant.query.filter_by(activity_id=act.id).count()

    groups = GroupInfo.query.filter(GroupInfo.activity_id.in_([a.id for a in activities])).all() if activities else []
    pending_confirm = TeamConfirmation.query.filter(
        TeamConfirmation.group_id.in_([g.id for g in groups]),
        TeamConfirmation.status == "pending",
    ).count() if groups else 0

    group_ids = [g.id for g in groups]
    tasks = Task.query.filter(Task.group_id.in_(group_ids)).all() if group_ids else []
    task_total = len(tasks)
    task_done = sum(1 for t in tasks if (t.progress or 0) >= 100 or t.status == "done")
    completion_rate = round(task_done / max(task_total, 1) * 100, 1)

    risk_count = 0
    overdue = 0
    now = datetime.utcnow()
    for t in tasks:
        if (t.progress or 0) >= 100:
            continue
        if t.deadline and t.deadline < now:
            overdue += 1
            risk_count += 1
        elif (t.progress or 0) < 30:
            risk_count += 1

    health_score = min(
        100,
        int(profile_rate * 0.35 + completion_rate * 0.35 + max(0, 100 - risk_count * 8) * 0.3),
    )
    level = "good" if health_score >= 75 else ("warning" if health_score >= 50 else "critical")

    breakdown = {
        "profile_weight": 0.35,
        "task_weight": 0.35,
        "risk_weight": 0.30,
        "profile_component": round(profile_rate * 0.35, 1),
        "task_component": round(completion_rate * 0.35, 1),
        "risk_component": round(max(0, 100 - risk_count * 8) * 0.3, 1),
    }

    return {
        "class_id": class_id,
        "class_name": cls.name,
        "health_score": health_score,
        "health_level": level,
        "breakdown": breakdown,
        "member_count": total,
        "profile_completion_rate": profile_rate,
        "profiles_done": with_profile,
        "activity_count": len(activities),
        "active_activity_count": len(active_acts),
        "participant_count": participants,
        "group_count": len(groups),
        "pending_confirmations": pending_confirm,
        "task_count": task_total,
        "task_completion_rate": completion_rate,
        "overdue_tasks": overdue,
        "risk_task_count": risk_count,
        "timeline": load_timeline(cls),
    }


def build_nudge_list(class_id: int) -> dict[str, Any]:
    """待催办学生名单（教师一键复制/站内提醒）."""
    member_ids = _active_member_ids(class_id)
    users = {u.id: u for u in User.query.filter(User.id.in_(member_ids)).all()} if member_ids else {}
    no_profile = []
    no_activity = []
    pending_team = []

    for uid in member_ids:
        user = users.get(uid)
        if not user:
            continue
        prof = UserProfile.query.filter_by(user_id=uid).first()
        if not prof or not (prof.active_tags_json and prof.active_tags_json != "[]"):
            no_profile.append({"user_id": uid, "name": user.name, "account": user.account, "reason": "未完善画像"})

        joined = TeamActivityParticipant.query.join(TeamActivity).filter(
            TeamActivity.class_id == class_id,
            TeamActivityParticipant.user_id == uid,
        ).count()
        if joined == 0:
            no_activity.append({"user_id": uid, "name": user.name, "account": user.account, "reason": "未参与任何班级活动"})

    activities = TeamActivity.query.filter_by(class_id=class_id).all()
    for act in activities:
        if act.status not in {"confirming", "preview", "published"}:
            continue
        groups = GroupInfo.query.filter_by(activity_id=act.id).all()
        for g in groups:
            for mid in g.member_list():
                if mid not in member_ids:
                    continue
                conf = TeamConfirmation.query.filter_by(group_id=g.id, user_id=mid).first()
                if conf and conf.status == "pending":
                    u = users.get(mid)
                    pending_team.append(
                        {
                            "user_id": mid,
                            "name": u.name if u else str(mid),
                            "account": u.account if u else "",
                            "reason": f"待确认队伍「{g.group_name}」",
                            "activity_id": act.id,
                            "group_id": g.id,
                        }
                    )

    items = no_profile + no_activity + pending_team
    seen = set()
    deduped = []
    for item in items:
        key = (item["user_id"], item["reason"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return {
        "class_id": class_id,
        "total": len(deduped),
        "items": deduped,
        "summary": {
            "no_profile": len(no_profile),
            "no_activity": len(no_activity),
            "pending_team": len(pending_team),
        },
    }
