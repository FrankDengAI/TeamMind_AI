"""班级人数分组建议与班级成员工具."""
from __future__ import annotations

from math import ceil

from app.services.ai_insights import class_grouping_insight


def suggest_group_sizes(total: int, preferred: int = 4, min_size: int = 3, max_size: int = 5) -> list[int]:
    """按班级人数生成尽量均匀的项目组规模."""
    total = int(total or 0)
    preferred = max(min_size, min(max_size, int(preferred or 4)))
    if total <= 0:
        return []
    if total <= max_size:
        return [total]

    group_count = max(1, round(total / preferred))
    if group_count < 3 and total / group_count > preferred:
        group_count = ceil(total / preferred)
    group_count = max(ceil(total / max_size), group_count)
    base = total // group_count
    extra = total % group_count
    sizes = [base + 1 if i < extra else base for i in range(group_count)]
    while min(sizes) < min_size and len(sizes) > 1:
        sizes = sorted(sizes, reverse=True)
        sizes[0] += sizes.pop()
    return sorted(sizes, reverse=True)


def build_grouping_advice(total: int, preferred: int = 4, *, use_llm: bool = False) -> dict:
    sizes = suggest_group_sizes(total, preferred)
    context = {"preferred_group_size": int(preferred or 4), "min_group_size": 3, "max_group_size": 5}
    return {
        "student_count": int(total or 0),
        "preferred_group_size": int(preferred or 4),
        "group_count": len(sizes),
        "sizes": sizes,
        "summary": "暂无可分组学生" if not sizes else f"建议分为 {len(sizes)} 组，人数分配为 {'/'.join(str(x) for x in sizes)}",
        "ai_analysis": class_grouping_insight(total, sizes, context, use_llm=use_llm),
    }
