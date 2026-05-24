"""初始任务分配算法."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class TaskAssignAlgorithm:
    """根据画像与模板分配任务."""

    def __init__(self):
        tpl_path = Path(__file__).resolve().parent.parent.parent / "data" / "task_templates.json"
        if tpl_path.exists():
            self.templates = json.loads(tpl_path.read_text(encoding="utf-8"))
        else:
            self.templates = self._default_templates()

    def _default_templates(self) -> dict:
        return {
            "product_dev": {
                "name": "产品开发",
                "tasks": [
                    {"name": "需求调研", "difficulty": 2, "role": "协调对接", "hours": 4, "depends": []},
                    {"name": "原型设计", "difficulty": 3, "role": "设计执行", "hours": 8, "depends": [0]},
                    {"name": "后端开发", "difficulty": 4, "role": "技术开发", "hours": 12, "depends": [1]},
                    {"name": "前端开发", "difficulty": 4, "role": "技术开发", "hours": 10, "depends": [1]},
                    {"name": "测试验收", "difficulty": 3, "role": "质量审核", "hours": 6, "depends": [2, 3]},
                ],
            },
            "research": {
                "name": "科研报告",
                "tasks": [
                    {"name": "文献综述", "difficulty": 3, "role": "数据支持", "hours": 8, "depends": []},
                    {"name": "实验设计", "difficulty": 4, "role": "技术开发", "hours": 10, "depends": [0]},
                    {"name": "数据分析", "difficulty": 4, "role": "数据支持", "hours": 8, "depends": [1]},
                    {"name": "论文撰写", "difficulty": 3, "role": "文案撰写", "hours": 12, "depends": [2]},
                ],
            },
            "activity": {
                "name": "活动策划",
                "tasks": [
                    {"name": "方案策划", "difficulty": 3, "role": "创意策划", "hours": 6, "depends": []},
                    {"name": "物料设计", "difficulty": 2, "role": "设计执行", "hours": 6, "depends": [0]},
                    {"name": "宣传推广", "difficulty": 3, "role": "对外对接", "hours": 8, "depends": [0]},
                    {"name": "现场执行", "difficulty": 2, "role": "执行落地", "hours": 8, "depends": [1, 2]},
                ],
            },
        }

    def assign(
        self,
        group_id: int,
        members: list[dict],
        template_key: str = "product_dev",
        custom_tasks: list | None = None,
        team_goal: str = "",
    ) -> list[dict[str, Any]]:
        tpl = self.templates.get(template_key, self.templates["product_dev"])
        tasks_def = custom_tasks or tpl["tasks"]
        sorted_members = sorted(members, key=lambda m: self._score(m, "skill"), reverse=True)
        assignments = []
        hours_map = {m["user_id"]: 0 for m in members}
        deadline_base = datetime.utcnow() + timedelta(days=14)

        for idx, tdef in enumerate(tasks_def):
            assignee, reason = self._pick_assignee(tdef, sorted_members, hours_map)
            if assignee is None:
                assignee = sorted_members[idx % len(sorted_members)]
                reason = "按轮询均衡分配，保证每人承担子任务"
            uid = assignee["user_id"]
            hours_map[uid] = hours_map.get(uid, 0) + tdef.get("hours", 2)
            base_desc = f"{team_goal or tpl['name']} - {tdef['name']}"
            assignments.append(
                {
                    "task_name": tdef["name"],
                    "description": f"{base_desc}\n【分配依据】{reason}",
                    "assign_reason": reason,
                    "difficulty": tdef.get("difficulty", 3),
                    "group_id": group_id,
                    "assignee_id": uid,
                    "role_required": tdef.get("role", "执行落地"),
                    "estimated_hours": tdef.get("hours", 2),
                    "depends_on": tdef.get("depends", []),
                    "deadline": (deadline_base + timedelta(days=idx * 3)).isoformat(),
                    "status": "pending",
                    "progress": 0,
                }
            )
        return assignments

    def _pick_assignee(self, tdef: dict, members: list, hours_map: dict) -> tuple[dict | None, str]:
        """匹配任务难度、角色偏好与当前工时负载."""
        difficulty = tdef.get("difficulty", 3)
        role = tdef.get("role", "")
        best, best_score = None, -1
        for m in members:
            skill = self._score(m, "skill") or 5
            if abs(skill - difficulty) > 2:
                continue
            role_match = 2 if m.get("pref_role") == role else 0
            tag_match = 1 if self._has_tag(m, role) else 0
            load_penalty = hours_map.get(m["user_id"], 0) * 0.5
            score = role_match + tag_match + skill - load_penalty
            if score > best_score:
                best_score = score
                best = m
        if best is None:
            fallback = min(members, key=lambda x: hours_map.get(x["user_id"], 0))
            hrs = hours_map.get(fallback["user_id"], 0)
            return fallback, (
                f"任务难度 {difficulty} 级，按当前累计工时最少者分配（已承担 {hrs:.0f}h），"
                f"保障工作量均衡"
            )
        pref = best.get("pref_role") or "未指定"
        hrs = hours_map.get(best["user_id"], 0)
        role_part = (
            f"角色偏好「{pref}」与任务要求「{role}」匹配"
            if pref == role
            else f"实操能力 {self._score(best, 'skill'):.1f} 与难度 {difficulty} 级适配"
        )
        reason = f"{role_part}；当前累计工时 {hrs:.0f}h，兼顾负载均衡"
        return best, reason

    def _score(self, member: dict, dim: str) -> float:
        return float(member.get(f"{dim}_final") or member.get(f"{dim}_score") or 0)

    def _has_tag(self, member: dict, name: str) -> bool:
        tags = (member.get("active_tags") or []) + (member.get("passive_tags") or [])
        for tag in tags:
            if isinstance(tag, dict) and tag.get("name") == name:
                return True
            if tag == name:
                return True
        return False
