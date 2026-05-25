"""AI 智能分析服务，DeepSeek 可用时调用大模型，不可用时稳定兜底."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import Config


def _call_deepseek_json(system_prompt: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if not Config.DEEPSEEK_ENABLED or not Config.DEEPSEEK_API_KEY:
        return None
    body = {
        "model": Config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    try:
        with httpx.Client(timeout=Config.DEEPSEEK_TIMEOUT) as client:
            resp = client.post(
                Config.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json=body,
            )
        resp.raise_for_status()
        content = (resp.json()["choices"][0]["message"]["content"] or "").strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
        data["source"] = "deepseek"
        data["model"] = Config.DEEPSEEK_MODEL
        return data
    except Exception as exc:  # noqa: BLE001
        return {"source": "fallback", "model": Config.DEEPSEEK_MODEL, "error": str(exc)}


def class_grouping_insight(total: int, sizes: list[int], context: dict[str, Any] | None = None, *, use_llm: bool = False) -> dict[str, Any]:
    context = context or {}
    fallback = _fallback_class_grouping_insight(total, sizes, context)
    if not use_llm:
        return fallback
    ai = _call_deepseek_json(
        "你是高校项目制学习的智能分组顾问。请只输出 JSON："
        "{summary:string,rationale:[string],risks:[string],recommendations:[string],teacher_actions:[string]}。"
        "分析要专业、简洁、可执行，不能编造学生不存在的信息。",
        {"student_count": total, "group_sizes": sizes, "context": context},
    )
    if not ai or ai.get("error"):
        fallback["source"] = "rule_fallback"
        if ai and ai.get("error"):
            fallback["error"] = ai["error"]
        return fallback
    return _normalize_insight(ai, fallback)


def activity_grouping_insight(activity: dict, groups: list[dict], *, use_llm: bool = False) -> dict[str, Any]:
    fallback = _fallback_activity_grouping_insight(activity, groups)
    if not use_llm:
        return fallback
    ai = _call_deepseek_json(
        "你是高校课程项目的 AI 分组复盘助手。请只输出 JSON："
        "{summary:string,rationale:[string],risks:[string],recommendations:[string],teacher_actions:[string]}。"
        "结合小组人数、均衡度、任务目标与角色覆盖给老师专业建议。",
        {"activity": activity, "groups": groups},
    )
    if not ai or ai.get("error"):
        fallback["source"] = "rule_fallback"
        if ai and ai.get("error"):
            fallback["error"] = ai["error"]
        return fallback
    return _normalize_insight(ai, fallback)


def group_ai_insight(
    group: dict,
    members: list[dict] | None = None,
    *,
    use_llm: bool = False,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    members = members or []
    fallback = _fallback_group_insight(group, members)
    if not use_llm:
        return fallback
    ctx = context or {}
    ai = _call_deepseek_json(
        "你是高校项目制学习的小组协作顾问。请只输出 JSON："
        "{summary:string,rationale:[string],risks:[string],recommendations:[string],teacher_actions:[string]}。"
        "针对该候选小组的成员画像、角色与均衡度给出可执行建议，勿编造未提供的学生信息。",
        {
            "group": group,
            "members": [
                {
                    "user_id": m.get("user_id"),
                    "pref_role": m.get("pref_role"),
                    "major": m.get("major"),
                    "knowledge_score": m.get("knowledge_final") or m.get("knowledge_score"),
                    "skill_score": m.get("skill_final") or m.get("skill_score"),
                    "collab_score": m.get("collab_final") or m.get("collab_score"),
                    "active_tags": (m.get("active_tags") or [])[:12],
                }
                for m in members
            ],
            "context": ctx,
        },
    )
    if not ai or ai.get("error"):
        fallback["source"] = "rule_fallback"
        if ai and ai.get("error"):
            fallback["error"] = ai["error"]
        return fallback
    return _normalize_insight(ai, fallback)


def task_assign_insight(
    assignments: list[dict],
    members: list[dict],
    *,
    team_goal: str = "",
    template_key: str = "product_dev",
    use_llm: bool = False,
) -> dict[str, Any]:
    fallback = {
        "source": "rule_fallback",
        "summary": "已根据成员技能与角色偏好完成初始任务分配。",
        "rationale": ["分配算法优先匹配任务所需角色与成员技能标签。", "工时与难度按模板默认值估算。"],
        "teacher_actions": ["锁定团队后请与学生确认分工是否合理。"],
    }
    if not use_llm:
        return fallback
    ai = _call_deepseek_json(
        "你是项目制课程的任务分工顾问。请只输出 JSON："
        "{summary:string,rationale:[string],task_notes:[{task_name:string,assignee_id:int,reason:string}],teacher_actions:[string]}。"
        "task_notes 需覆盖每条 assignment，reason 为 1-2 句可给学生看的分配依据。",
        {
            "assignments": assignments,
            "members": members,
            "team_goal": team_goal,
            "template_key": template_key,
        },
    )
    if not ai or ai.get("error"):
        fallback["source"] = "rule_fallback"
        return fallback
    return {**fallback, **ai, "source": ai.get("source", "deepseek")}


def task_adjust_insight(
    adjust_result: dict,
    tasks: list[dict],
    members: list[dict],
    behavior_summary: dict,
    *,
    use_llm: bool = False,
) -> dict[str, Any]:
    fallback = {
        "source": "rule_fallback",
        "summary": f"共生成 {len(adjust_result.get('suggestions') or [])} 条调优建议。",
        "rationale": ["依据成员进度、提交状态与同伴反馈生成。"],
        "teacher_actions": ["在任务看板中逐条确认或驳回系统建议。"],
    }
    if not use_llm:
        return fallback
    ai = _call_deepseek_json(
        "你是团队协作的任务调优顾问。请只输出 JSON："
        "{summary:string,rationale:[string],risks:[string],teacher_actions:[string]}。"
        "结合行为摘要与系统建议，给老师一段整体判断与优先处理顺序。",
        {
            "adjust_result": adjust_result,
            "tasks": tasks,
            "members": members,
            "behavior_summary": behavior_summary,
        },
    )
    if not ai or ai.get("error"):
        return fallback
    return _normalize_insight(ai, fallback)


def team_report_insight(
    report: dict,
    group: dict,
    tasks: list[dict],
    *,
    use_llm: bool = False,
) -> dict[str, Any]:
    fallback = {
        "source": "rule_fallback",
        "summary": f"团队完成率 {report.get('completion_rate', 0)}%，质量分 {report.get('quality_score', 0)}，风险等级 {report.get('risk_level', 'unknown')}。",
        "rationale": ["指标由任务进度、均衡分与迟交行为综合计算。"],
        "teacher_actions": ["关注高风险小组并安排复盘会议。"],
    }
    if not use_llm:
        return fallback
    ai = _call_deepseek_json(
        "你是教学评估顾问。请只输出 JSON："
        "{summary:string,rationale:[string],risks:[string],recommendations:[string],teacher_actions:[string]}。"
        "为教师撰写 3-5 句团队质量报告叙事，客观、可执行。",
        {"report": report, "group": group, "tasks": tasks},
    )
    if not ai or ai.get("error"):
        return fallback
    return _normalize_insight(ai, fallback)


def _fallback_group_insight(group: dict, members: list[dict]) -> dict[str, Any]:
    roles = [m.get("pref_role") for m in members if m.get("pref_role")]
    skills = []
    for m in members:
        skills.extend([t.get("name") for t in (m.get("active_tags") or []) if isinstance(t, dict) and t.get("dimension") == "skill"])
    return {
        "source": "rule_fallback",
        "model": None,
        "summary": f"{group.get('group_name', '该小组')}共 {len(group.get('member_ids') or [])} 人，技能均分 {group.get('avg_skill', 0)}，适合进入预沟通确认。",
        "rationale": [
            f"角色覆盖：{'、'.join(list(dict.fromkeys(roles))[:4]) or '待根据画像继续细化'}。",
            f"技能标签覆盖：{'、'.join(list(dict.fromkeys(skills))[:5]) or '暂无显著技能标签'}。",
            f"知识/技能/协作均分为 {group.get('avg_knowledge', 0)}/{group.get('avg_skill', 0)}/{group.get('avg_collab', 0)}。",
        ],
        "risks": ["若组内角色重复较多，建议老师在预沟通阶段引导重新认领职责。"],
        "recommendations": ["先确认每位成员的首选角色，再把任务拆成技术、产品、数据、文档与汇报子任务。"],
        "teacher_actions": ["关注低画像完整度成员", "要求小组在锁定前提交一次角色确认"],
    }


def _fallback_class_grouping_insight(total: int, sizes: list[int], context: dict[str, Any]) -> dict[str, Any]:
    spread = (max(sizes) - min(sizes)) if sizes else 0
    return {
        "source": "rule_fallback",
        "model": None,
        "summary": "当前班级人数适合进行均匀项目分组。" if sizes else "当前暂无可分组学生。",
        "rationale": [
            f"系统建议分为 {len(sizes)} 组，人数为 {'/'.join(str(x) for x in sizes) or '0'}。",
            f"最大组与最小组人数差为 {spread}，可降低组间工作量不均。",
            f"默认参考每组 {context.get('preferred_group_size') or 4} 人，符合 10-20 人班级的小组项目组织方式。",
        ],
        "risks": ["人数较少的小组需要老师关注任务拆分，避免承担同等任务量。"] if spread else [],
        "recommendations": ["先按人数均匀分组，再结合画像进行角色互补。", "建议分组后保留预沟通阶段，让学生确认角色与任务偏好。"],
        "teacher_actions": ["检查未录入画像学生", "发布活动后提醒学生同步标签", "锁定前处理微调申请"],
    }


def _fallback_activity_grouping_insight(activity: dict, groups: list[dict]) -> dict[str, Any]:
    avg_balance = round(sum(float(g.get("balance_score") or 0) for g in groups) / max(len(groups), 1), 2)
    return {
        "source": "rule_fallback",
        "model": None,
        "summary": f"已为活动“{activity.get('title') or '未命名活动'}”生成 {len(groups)} 个候选小组，平均均衡度 {avg_balance}。",
        "rationale": [
            "候选分组已结合成员画像、角色偏好、技能标签和任务目标进行互补匹配。",
            "班级绑定活动会自动限定在本班 active 成员中，避免跨班级误分配。",
            "小组人数按班级规模尽量均匀，降低组间协作负载差异。",
        ],
        "risks": ["画像缺失或标签过少的学生可能降低匹配精度。"],
        "recommendations": ["进入预沟通阶段后，优先收集学生对角色和任务偏好的反馈。", "锁定前重点查看均衡度偏低的小组。"],
        "teacher_actions": ["查看每组 AI 分析", "处理微调申请", "锁定正式团队后再分配任务"],
    }


def _normalize_insight(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    out = {**fallback, **data}
    for key in ("rationale", "risks", "recommendations", "teacher_actions"):
        value = out.get(key)
        if isinstance(value, str):
            out[key] = [value]
        elif not isinstance(value, list):
            out[key] = fallback.get(key, [])
    out["summary"] = str(out.get("summary") or fallback["summary"])
    return out
