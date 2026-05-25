"""任务分配/调优的大模型增强（供 task API 与 admin ops 复用）."""
from __future__ import annotations

from app.middleware.entitlement import paywall_response
from app.services.ai_insights import task_adjust_insight, task_assign_insight
from app.services.entitlement_service import PaywallError, consume_ai_points, get_entitlements


def enrich_assignments_with_ai(
    user_id: int,
    assignments: list[dict],
    members: list[dict],
    *,
    team_goal: str = "",
    template_key: str = "product_dev",
    use_ai: bool = False,
) -> tuple[list[dict], dict | None]:
    if not use_ai:
        return assignments, None
    ent = get_entitlements(user_id)
    if not ent["flags"].get("activity_llm_insight"):
        raise PaywallError("任务 AI 分工说明需升级专业版", feature="task.assign")
    consume_ai_points(user_id, "task.assign")
    insight = task_assign_insight(
        assignments, members, team_goal=team_goal, template_key=template_key, use_llm=True
    )
    notes = {n.get("task_name"): n for n in (insight.get("task_notes") or []) if isinstance(n, dict)}
    for item in assignments:
        note = notes.get(item.get("task_name")) or {}
        reason = (note.get("reason") or "").strip()
        if reason:
            item["assign_reason"] = reason
            item["description"] = f"{item.get('description', '')}\n【AI 依据】{reason}".strip()
    return assignments, insight


def enrich_adjust_with_ai(
    user_id: int,
    result: dict,
    tasks: list[dict],
    members: list[dict],
    behavior_summary: dict,
    *,
    use_ai: bool = False,
) -> dict:
    if not use_ai:
        return result
    ent = get_entitlements(user_id)
    if not ent["flags"].get("activity_llm_insight"):
        raise PaywallError("任务调优 AI 解读需升级专业版", feature="task.adjust")
    consume_ai_points(user_id, "task.adjust")
    result["ai_insight"] = task_adjust_insight(result, tasks, members, behavior_summary=behavior_summary, use_llm=True)
    return result
