"""班级 Copilot — 教师自然语言问答（DeepSeek + 规则兜底）."""
from __future__ import annotations

import json
from typing import Any

from app.models import BehaviorLog, ClassMembership, Classroom, GroupInfo, Task, TeamActivity, User, UserProfile
from app.services.ai_insights import _call_deepseek_json
from app.services.classroom_insights import build_class_health, build_nudge_list


SUGGESTED_QUESTIONS = [
    "本周谁可能拖慢项目进度？",
    "该催哪些学生完善画像或确认队伍？",
    "当前班级健康度主要短板是什么？",
    "分组时需要注意哪些专业或角色风险？",
]


def get_suggested_questions(class_id: int) -> list[str]:
    health = build_class_health(class_id)
    out = list(SUGGESTED_QUESTIONS)
    if (health.get("overdue_tasks") or 0) > 0:
        out.insert(0, f"有 {health['overdue_tasks']} 个逾期任务，应先处理哪些组？")
    if (health.get("profile_completion_rate") or 100) < 80:
        out.insert(0, "哪些学生尚未完善画像？")
    return out[:6]


def _student_evidence(user_id: int) -> dict[str, Any]:
    prof = UserProfile.query.filter_by(user_id=user_id).order_by(UserProfile.create_time.desc()).first()
    tags = []
    if prof and prof.active_tags_json:
        try:
            raw = json.loads(prof.active_tags_json)
            tags = [t.get("name") if isinstance(t, dict) else str(t) for t in raw if t]
        except (TypeError, json.JSONDecodeError):
            tags = []
    log_count = BehaviorLog.query.filter_by(user_id=user_id).count()
    user = User.query.get(user_id)
    return {
        "user_id": user_id,
        "name": user.name if user else str(user_id),
        "account": user.account if user else "",
        "tag_names": tags[:8],
        "behavior_log_count": log_count,
        "skill_score": float(prof.skill_final or prof.skill_score or 0) if prof else None,
        "profile_complete": bool(tags),
    }


def _class_context(class_id: int) -> dict[str, Any]:
    health = build_class_health(class_id)
    nudges = build_nudge_list(class_id)
    cls = Classroom.query.get(class_id)
    activities = TeamActivity.query.filter_by(class_id=class_id).order_by(TeamActivity.create_time.desc()).limit(5).all()
    act_brief = [{"id": a.id, "title": a.title, "status": a.status, "mode": a.mode} for a in activities]
    members = ClassMembership.query.filter_by(class_id=class_id, status="active").count()
    return {
        "class": {"id": class_id, "name": cls.name if cls else "", "course": cls.course_name if cls else ""},
        "health": health,
        "nudges_summary": nudges.get("summary"),
        "nudge_samples": nudges.get("items", [])[:8],
        "recent_activities": act_brief,
        "active_members": members,
    }


def _build_evidence(focus_items: list[dict]) -> list[dict[str, Any]]:
    evidence = []
    for item in focus_items:
        uid = item.get("user_id")
        if not uid and item.get("name"):
            u = User.query.filter_by(name=item.get("name")).first()
            uid = u.id if u else None
        if not uid:
            continue
        ev = _student_evidence(uid)
        ev["reason"] = item.get("reason") or ""
        evidence.append(ev)
    return evidence


def _rule_answer(question: str, ctx: dict[str, Any]) -> dict[str, Any]:
    q = (question or "").strip()
    health = ctx.get("health") or {}
    lines = []
    focus = []
    if "拖" in q or "风险" in q or "落后" in q:
        lines.append(
            f"当前班级任务完成率 {health.get('task_completion_rate', 0)}%，"
            f"逾期任务 {health.get('overdue_tasks', 0)} 个，建议优先查看指挥舱预警。"
        )
        for item in ctx.get("nudge_samples") or []:
            if "任务" in item.get("reason", "") or "画像" in item.get("reason", ""):
                lines.append(f"- {item.get('name')}：{item.get('reason')}")
                focus.append(item)
    elif "催" in q or "谁没" in q:
        n = ctx.get("nudges_summary") or {}
        lines.append(
            f"待关注：未完善画像 {n.get('no_profile', 0)} 人，未参与活动 {n.get('no_activity', 0)} 人，"
            f"待确认队伍 {n.get('pending_team', 0)} 人。可在班级页使用「一键催办」名单。"
        )
        focus = list(ctx.get("nudge_samples") or [])[:5]
    elif "分组" in q or "组队" in q:
        lines.append(
            f"班级健康分 {health.get('health_score', 0)}，建议组数可参考分组建议页；"
            f"进行中的活动 {health.get('active_activity_count', 0)} 个。"
        )
        bd = health.get("breakdown") or {}
        if bd:
            lines.append(
                f"健康分构成：画像 {bd.get('profile_component')} + 任务 {bd.get('task_component')} + 风险缓冲 {bd.get('risk_component')}"
            )
    else:
        lines.append(
            f"「{ctx.get('class', {}).get('name', '本班')}」共 {health.get('member_count', 0)} 名学生，"
            f"画像完成率 {health.get('profile_completion_rate', 0)}%，任务完成率 {health.get('task_completion_rate', 0)}%。"
        )
        lines.append("你可以问我：谁可能拖进度、该催哪些学生、本周怎么拆任务、分组要注意什么。")
    evidence = _build_evidence(focus or (ctx.get("nudge_samples") or [])[:3])
    return {
        "answer": "\n".join(lines),
        "source": "rule",
        "suggestions": ["查看待催办名单", "打开分组建议", "进入活动工作台"],
        "focus_students": focus,
        "evidence": evidence,
        "suggested_questions": get_suggested_questions(ctx.get("class", {}).get("id") or 0),
    }


def ask_class_copilot(
    class_id: int,
    question: str,
    *,
    use_llm: bool = True,
    history: list[dict] | None = None,
) -> dict[str, Any]:
    ctx = _class_context(class_id)
    fallback = _rule_answer(question, ctx)
    fallback["suggested_questions"] = get_suggested_questions(class_id)
    hist = history or []
    if not use_llm:
        return fallback
    ai = _call_deepseek_json(
        "你是高校项目制学习平台的班级助教 Copilot。根据提供的班级数据回答教师问题。"
        "输出 JSON：{answer:string, suggestions:[string], focus_students:[{user_id?,name,reason}]}。"
        "不要编造不存在的学生；数据不足时明确说明并给可执行建议。",
        {"question": question, "context": ctx, "history": hist[-6:]},
    )
    if not ai or ai.get("error"):
        fallback["source"] = "rule_fallback"
        if ai and ai.get("error"):
            fallback["llm_error"] = ai["error"]
        return fallback
    focus = ai.get("focus_students") or []
    return {
        "answer": ai.get("answer") or ai.get("summary") or fallback["answer"],
        "suggestions": ai.get("suggestions") or fallback.get("suggestions", []),
        "focus_students": focus,
        "evidence": _build_evidence(focus) or fallback.get("evidence", []),
        "source": ai.get("source", "deepseek"),
        "suggested_questions": get_suggested_questions(class_id),
    }
