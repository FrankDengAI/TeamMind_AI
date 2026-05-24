"""任务创建相关共享逻辑."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable

from app import db
from app.models import Task


def parse_deadline(value):
    """兼容日期或 ISO 时间字符串，解析失败时返回 None."""
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.fromisoformat(text + "T23:59:59")
        except ValueError:
            return None


def create_assigned_tasks(group_id: int, assignments: Iterable[dict]) -> list[Task]:
    """按算法输出创建任务，并把依赖索引映射为真实任务 ID.

    算法返回的 ``depends_on`` 是同批任务的下标，必须等所有任务 flush 后
    再转换成数据库 ID。这里不修改原始 assignments，避免依赖信息被提前丢失。
    """
    assignment_list = [dict(item or {}) for item in assignments]
    created: list[Task] = []
    id_map: dict[int, int] = {}

    for index, assignment in enumerate(assignment_list):
        task = Task(
            task_name=assignment["task_name"],
            description=assignment["description"],
            difficulty=assignment["difficulty"],
            group_id=group_id,
            assignee_id=assignment["assignee_id"],
            role_required=assignment.get("role_required"),
            estimated_hours=assignment.get("estimated_hours", 2),
            deadline=parse_deadline(assignment.get("deadline")),
            status="pending",
            progress=0,
            depends_on=json.dumps([]),
        )
        db.session.add(task)
        db.session.flush()
        id_map[index] = task.id
        created.append(task)

    for index, task in enumerate(created):
        dependency_indexes = assignment_list[index].get("depends_on") or []
        dependency_ids = []
        for item in dependency_indexes:
            try:
                dep_index = int(item)
            except (TypeError, ValueError):
                continue
            if dep_index in id_map:
                dependency_ids.append(id_map[dep_index])
        task.depends_on = json.dumps(dependency_ids)

    return created
