"""组内角色分配：基于画像推荐并支持多样性."""
from __future__ import annotations

from datetime import datetime

# 常见项目角色池（与任务模板 role 字段对齐）
ROLE_POOL = [
    "技术开发",
    "设计执行",
    "协调对接",
    "数据支持",
    "质量审核",
    "创意策划",
    "文案撰写",
    "执行落地",
    "对外对接",
]


def _parse_pref_role(pref: str | None) -> str:
    if not pref:
        return "执行落地"
    pref = pref.strip()
    for r in ROLE_POOL:
        if r in pref or pref in r:
            return r
    return pref if pref else "执行落地"


def assign_roles_for_group(member_profiles: list[dict]) -> list[dict]:
    """
    为组内成员分配角色，尽量不重复.
    member_profiles: [{user_id, pref_role, skill_score, ...}, ...]
    """
    used_roles: set[str] = set()
    assignments = []

    # 按技能分排序，高技能优先选稀缺角色
    sorted_members = sorted(
        member_profiles,
        key=lambda m: float(m.get("skill_final") or m.get("skill_score") or 0),
        reverse=True,
    )

    for m in sorted_members:
        uid = m.get("user_id")
        preferred = _parse_pref_role(m.get("pref_role"))
        role = preferred
        reason = f"匹配画像偏好角色「{m.get('pref_role') or preferred}」"

        if preferred in used_roles:
            # 找未使用的池中角色
            fallback = None
            for r in ROLE_POOL:
                if r not in used_roles:
                    fallback = r
                    break
            if fallback:
                role = fallback
                reason = f"原偏好「{preferred}」已被占用，调整为「{fallback}」以保证组内角色多样"
            else:
                role = preferred
                reason = "组内人数较多，允许角色重复"

        used_roles.add(role)
        assignments.append(
            {
                "user_id": uid,
                "role": role,
                "source": "auto",
                "reason": reason,
                "assigned_at": datetime.utcnow().isoformat(),
            }
        )

    return assignments


def get_member_roles_from_config(config: dict | None) -> list[dict]:
    if not config:
        return []
    return config.get("member_roles") or []


def role_map_from_config(config: dict | None) -> dict[int, str]:
    """user_id -> role"""
    out = {}
    for item in get_member_roles_from_config(config):
        uid = item.get("user_id")
        if uid is not None:
            out[int(uid)] = item.get("role", "")
    return out
