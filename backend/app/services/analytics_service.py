"""团队项目分析：进度、积极性、截止预警、负载均衡."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except (TypeError, ValueError):
        return None


def assess_task_risk(task: dict, now: datetime | None = None) -> dict[str, Any]:
    """单任务截止与进度风险."""
    now = now or datetime.utcnow()
    deadline = _parse_dt(task.get("deadline"))
    progress = int(task.get("progress") or 0)
    status = task.get("status") or "pending"
    hours = float(task.get("estimated_hours") or 2)
    created = _parse_dt(task.get("create_time")) or now

    if progress >= 100 or status == "done":
        return {
            "level": "done",
            "label": "已完成",
            "days_left": 0,
            "on_track": True,
            "message": "任务已完成",
        }

    if not deadline:
        return {
            "level": "normal",
            "label": "正常",
            "days_left": None,
            "on_track": True,
            "message": "未设置截止日期",
        }

    days_left = (deadline - now).total_seconds() / 86400
    elapsed_days = max((now - created).total_seconds() / 86400, 0.1)
    velocity = progress / elapsed_days if elapsed_days > 0 else 0
    remaining = max(100 - progress, 0)
    eta_days = remaining / velocity if velocity > 0.01 else 999
    on_track = eta_days <= max(days_left, 0) + 0.5

    if days_left < 0:
        level, label, msg = "critical", "已逾期", f"已超期 {abs(int(days_left))} 天，请立即处理"
    elif days_left <= 2 and progress < 70:
        level, label, msg = "critical", "紧急", f"剩余 {max(0, int(days_left))} 天，进度仅 {progress}%"
    elif days_left <= 5 and (progress < 50 or not on_track):
        level, label, msg = "warning", "预警", f"预计难以按期完成（剩余 {max(0, int(days_left))} 天）"
    elif progress < 30 and days_left <= 7:
        level, label, msg = "warning", "滞后", "进度偏慢，建议加快或申请协助"
    else:
        level, label, msg = "normal", "正常", f"剩余 {max(0, int(days_left))} 天，进展正常"

    return {
        "level": level,
        "label": label,
        "days_left": round(days_left, 1),
        "on_track": on_track,
        "eta_days": round(min(eta_days, 999), 1),
        "velocity_per_day": round(velocity, 2),
        "message": msg,
    }


def assess_member_engagement(
    user_id: int,
    tasks: list[dict],
    logs: list,
    now: datetime | None = None,
) -> dict[str, Any]:
    """成员积极性与协作表现."""
    now = now or datetime.utcnow()
    my_tasks = [t for t in tasks if t.get("assignee_id") == user_id]
    my_logs = [
        l
        for l in logs
        if (l.user_id if hasattr(l, "user_id") else l.get("user_id")) == user_id
    ]

    if not my_tasks and not my_logs:
        return {
            "engagement_score": 0,
            "engagement_level": "unknown",
            "engagement_label": "暂无数据",
            "avg_progress": 0,
            "completed_tasks": 0,
            "total_tasks": 0,
            "active_days": 0,
            "last_active": None,
            "tendency": "normal",
        }

    total = len(my_tasks)
    done = sum(1 for t in my_tasks if (t.get("progress") or 0) >= 100)
    avg_prog = sum(t.get("progress") or 0 for t in my_tasks) / max(total, 1)

    active_days = set()
    late_count = 0
    feedback_count = 0
    update_count = len(my_logs)
    for log in my_logs:
        rt = log.record_time if hasattr(log, "record_time") else log.get("record_time")
        dt = _parse_dt(rt)
        if dt:
            active_days.add(dt.date())
        st = log.submit_status if hasattr(log, "submit_status") else log.get("submit_status")
        if st == "late":
            late_count += 1
        event_type = log.event_type if hasattr(log, "event_type") else log.get("event_type")
        if event_type == "task_feedback":
            feedback_count += 1

    last_active = None
    if my_logs:
        times = [
            _parse_dt(l.record_time if hasattr(l, "record_time") else l.get("record_time"))
            for l in my_logs
        ]
        times = [t for t in times if t]
        if times:
            last_active = max(times).isoformat()

    days_since = 999
    if last_active:
        days_since = (now - _parse_dt(last_active)).days

    score = 50
    score += min(avg_prog * 0.3, 30)
    score += min(len(active_days) * 5, 20)
    score += done * 5
    score -= late_count * 10
    score -= feedback_count * 8
    if days_since > 7:
        score -= 25
    elif days_since > 3:
        score -= 10
    score = max(0, min(100, int(score)))

    if score >= 75:
        level, label = "high", "积极"
        tendency = "positive"
    elif score >= 45:
        level, label = "medium", "一般"
        tendency = "normal"
    else:
        level, label = "low", "需关注"
        tendency = "negative"

    return {
        "engagement_score": score,
        "engagement_level": level,
        "engagement_label": label,
        "avg_progress": round(avg_prog, 1),
        "completed_tasks": done,
        "total_tasks": total,
        "active_days": len(active_days),
        "update_count": update_count,
        "late_count": late_count,
        "feedback_count": feedback_count,
        "last_active": last_active,
        "days_since_active": days_since if last_active else None,
        "tendency": tendency,
    }


def build_group_dashboard(
    group_dict: dict,
    tasks: list[dict],
    members_raw: list[dict],
    logs: list,
) -> dict[str, Any]:
    """构建团队项目看板（含预警）."""
    now = datetime.utcnow()
    task_risks = []
    alerts = []
    critical_count = warning_count = 0

    for t in tasks:
        risk = assess_task_risk(t, now)
        item = {**t, "risk": risk}
        task_risks.append(item)
        if risk["level"] == "critical":
            critical_count += 1
            alerts.append(
                {
                    "type": "deadline",
                    "level": "critical",
                    "task_id": t.get("id"),
                    "task_name": t.get("task_name"),
                    "assignee_id": t.get("assignee_id"),
                    "message": risk["message"],
                }
            )
        elif risk["level"] == "warning":
            warning_count += 1
            alerts.append(
                {
                    "type": "deadline",
                    "level": "warning",
                    "task_id": t.get("id"),
                    "task_name": t.get("task_name"),
                    "assignee_id": t.get("assignee_id"),
                    "message": risk["message"],
                }
            )

    members_out = []
    workload = {}
    for m in members_raw:
        uid = m.get("user", {}).get("id") if m.get("user") else None
        if not uid:
            continue
        m_tasks = m.get("tasks") or []
        engagement = assess_member_engagement(uid, tasks, logs, now)
        hours = sum(float(t.get("estimated_hours") or 2) for t in m_tasks)
        workload[uid] = hours
        if engagement["engagement_level"] == "low":
            alerts.append(
                {
                    "type": "engagement",
                    "level": "warning",
                    "user_id": uid,
                    "user_name": m.get("user", {}).get("name"),
                    "message": f"{m.get('user', {}).get('name', '成员')} 协作积极性偏低，建议跟进",
                }
            )
        if engagement.get("feedback_count"):
            alerts.append(
                {
                    "type": "task_feedback",
                    "level": "warning",
                    "user_id": uid,
                    "user_name": m.get("user", {}).get("name"),
                    "message": f"{m.get('user', {}).get('name', '成员')} 已提交 {engagement.get('feedback_count')} 条任务负载/适配反馈，请在调优时关注",
                }
            )
        members_out.append({**m, "engagement": engagement, "workload_hours": round(hours, 1)})

    if workload:
        vals = list(workload.values())
        if max(vals) - min(vals) > 6:
            alerts.append(
                {
                    "type": "workload",
                    "level": "warning",
                    "message": "团队工时负载不均衡，建议重新分工",
                }
            )

    completion = 0
    if tasks:
        completion = sum(t.get("progress") or 0 for t in tasks) / len(tasks)

    alerts.sort(key=lambda a: 0 if a.get("level") == "critical" else 1)

    return {
        "group": group_dict,
        "grouping_explain": group_dict.get("complement_note") or "",
        "supervision_note": "成员可在同一平台查看彼此任务完成率与截止状态，实现透明进度追踪与互相监督。",
        "summary": {
            "completion_rate": round(completion, 1),
            "task_total": len(tasks),
            "task_done": sum(1 for t in tasks if (t.get("progress") or 0) >= 100),
            "critical_risks": critical_count,
            "warning_risks": warning_count,
            "alert_count": len(alerts),
            "member_count": len(members_out),
            "low_engagement_members": sum(1 for m in members_out if m.get("engagement", {}).get("engagement_level") == "low"),
            "feedback_count": sum(m.get("engagement", {}).get("feedback_count", 0) for m in members_out),
        },
        "members": members_out,
        "tasks": task_risks,
        "alerts": alerts[:20],
        "workload": workload,
        "generated_at": now.isoformat(),
    }


def build_platform_dashboard(groups, all_tasks, users_with_profile) -> dict[str, Any]:
    """管理端全平台指挥舱."""
    now = datetime.utcnow()
    alerts = []
    at_risk = 0
    low_engagement = 0

    for t in all_tasks:
        risk = assess_task_risk(t.to_dict() if hasattr(t, "to_dict") else t, now)
        td = t.to_dict() if hasattr(t, "to_dict") else t
        if risk["level"] in ("critical", "warning"):
            at_risk += 1
            if len(alerts) < 30:
                alerts.append(
                    {
                        "type": "task",
                        "level": risk["level"],
                        "group_id": td.get("group_id"),
                        "task_name": td.get("task_name"),
                        "message": risk["message"],
                    }
                )

    group_summaries = []
    for g in groups:
        gd = g.to_dict() if hasattr(g, "to_dict") else g
        gid = gd.get("id")
        g_tasks = [
            t.to_dict() if hasattr(t, "to_dict") else t
            for t in all_tasks
            if (t.group_id if hasattr(t, "group_id") else t.get("group_id")) == gid
        ]
        comp = sum(t.get("progress", 0) for t in g_tasks) / max(len(g_tasks), 1) if g_tasks else 0
        risks = sum(
            1
            for t in g_tasks
            if assess_task_risk(t, now)["level"] in ("critical", "warning")
        )
        group_summaries.append(
            {
                "group": gd,
                "task_count": len(g_tasks),
                "completion_rate": round(comp, 1),
                "risk_count": risks,
            }
        )

    return {
        "at_risk_tasks": at_risk,
        "low_engagement_members": low_engagement,
        "alerts": alerts,
        "group_summaries": sorted(group_summaries, key=lambda x: -x["risk_count"]),
        "generated_at": now.isoformat(),
    }
