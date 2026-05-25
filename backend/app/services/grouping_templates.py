"""分组策略模板库 — Phase A."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

GROUPING_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "heterogeneous_balanced",
        "name": "异构互补（默认）",
        "name_en": "Heterogeneous (balanced)",
        "description": "技能高者作种子，按专业/角色/标签互补填充，组间能力尽量均衡。",
        "tier": "free",
        "mode": "heterogeneous",
        "priority": "skill",
        "constraints": {},
    },
    {
        "id": "homogeneous_skill",
        "name": "同质分组（按技能）",
        "name_en": "Homogeneous by skill",
        "description": "能力相近的学生分在一组，适合分层教学或竞赛训练。",
        "tier": "free",
        "mode": "homogeneous",
        "priority": "skill",
        "constraints": {},
    },
    {
        "id": "role_quota",
        "name": "角色配额分组",
        "name_en": "Role quota",
        "description": "尽量保证每组覆盖技术、设计、文档等角色方向。",
        "tier": "pro",
        "mode": "heterogeneous",
        "priority": "role",
        "constraints": {"min_roles_per_group": 2},
    },
    {
        "id": "major_diverse",
        "name": "专业交叉分组",
        "name_en": "Cross-major",
        "description": "优先打散同一专业，促进跨学科协作。",
        "tier": "pro",
        "mode": "heterogeneous",
        "priority": "major",
        "constraints": {"max_same_major_ratio": 0.5},
    },
    {
        "id": "task_driven",
        "name": "任务标签驱动",
        "name_en": "Task-tag driven",
        "description": "结合活动必填标签与技能，适合任务驱动自动组队。",
        "tier": "pro",
        "mode": "task_auto",
        "priority": "skill",
        "constraints": {},
    },
    {
        "id": "random_balanced",
        "name": "随机 + 均衡微调",
        "name_en": "Random + balance",
        "description": "先随机分配再微调组间技能差，适合破冰周。",
        "tier": "free",
        "mode": "random",
        "priority": "skill",
        "constraints": {},
    },
]


def list_templates(*, plan_code: str = "free") -> list[dict[str, Any]]:
    tier_rank = {"free": 0, "pro": 1, "plus": 2}
    user_rank = tier_rank.get(plan_code, 0)
    out = []
    for tpl in GROUPING_TEMPLATES:
        need = tier_rank.get(tpl.get("tier", "free"), 0)
        item = deepcopy(tpl)
        item["locked"] = user_rank < need
        out.append(item)
    return out


def resolve_template(template_id: str | None, *, fallback_mode: str = "heterogeneous") -> dict[str, Any]:
    if template_id:
        for tpl in GROUPING_TEMPLATES:
            if tpl["id"] == template_id:
                return deepcopy(tpl)
    for tpl in GROUPING_TEMPLATES:
        if tpl["mode"] == fallback_mode:
            return deepcopy(tpl)
    return deepcopy(GROUPING_TEMPLATES[0])


def template_to_group_config(template_id: str | None, base: dict | None = None) -> dict[str, Any]:
    tpl = resolve_template(template_id, fallback_mode=(base or {}).get("mode", "heterogeneous"))
    cfg = dict(base or {})
    cfg["template_id"] = tpl["id"]
    cfg["template_name"] = tpl["name"]
    cfg["mode"] = tpl["mode"]
    cfg["priority"] = tpl.get("priority", "skill")
    cfg["constraints"] = tpl.get("constraints", {})
    return cfg
