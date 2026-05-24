"""异构智能分组算法 - 贪心 + 均衡微调."""
import json
import math
from typing import Any

from app.config import Config


class GroupingAlgorithm:
    """基于三维画像的互补分组."""

    def create_groups(
        self,
        profiles: list[dict],
        group_size: int = 4,
        mode: str = "heterogeneous",
        priority: str = "skill",
        task_requirements: dict | None = None,
        target_sizes: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        执行分组.
        :param profiles: 含 user_id, skill_score, knowledge_score, collab_score 等
        """
        if len(profiles) > Config.MAX_GROUP_USERS:
            raise ValueError(f"最多支持 {Config.MAX_GROUP_USERS} 人")
        if group_size < 2 or group_size > 8:
            group_size = Config.DEFAULT_GROUP_SIZE

        n = len(profiles)
        if n < group_size:
            raise ValueError("人数不足无法分组")

        if target_sizes:
            target_sizes = [int(x) for x in target_sizes if int(x) > 0]
            if sum(target_sizes) != n:
                target_sizes = None
        num_groups = len(target_sizes) if target_sizes else math.ceil(n / group_size)
        target_sizes = target_sizes or [group_size] * num_groups
        requirements = task_requirements or {}
        sorted_profiles = sorted(
            profiles,
            key=lambda p: self._score(p, "skill") + self._task_fit(p, requirements),
            reverse=True,
        )

        groups: list[dict] = [
            {"members": [], "skills": set(), "roles": [], "majors": [], "styles": set(), "tags": set()}
            for _ in range(num_groups)
        ]

        # 种子分配
        seeds = sorted_profiles[:num_groups]
        rest = sorted_profiles[num_groups:]
        for i, seed in enumerate(seeds):
            self._add_member(groups[i], seed)

        # 互补填充
        for user in rest:
            best_gi = 0
            best_gain = -999
            for gi, g in enumerate(groups):
                if len(g["members"]) >= target_sizes[gi]:
                    continue
                gain = self._complement_gain(user, g, mode) + self._task_fit(user, requirements)
                if gain > best_gain:
                    best_gain = gain
                    best_gi = gi
            self._add_member(groups[best_gi], user)

        # 均衡微调
        audit = []
        for _ in range(20):
            if self._check_balance(groups, group_size):
                break
            self._swap_balance(groups, audit)

        result_groups = []
        complement_notes = []
        for i, g in enumerate(groups):
            members = g["members"]
            if not members:
                continue
            avg_k = sum(self._score(m, "knowledge") for m in members) / len(members)
            avg_s = sum(self._score(m, "skill") for m in members) / len(members)
            avg_c = sum(self._score(m, "collab") for m in members) / len(members)
            note = self._complement_note(g, requirements)
            complement_notes.append(note)
            result_groups.append(
                {
                    "group_name": f"第{i + 1}组",
                    "member_ids": [m["user_id"] for m in members],
                    "members": members,
                    "avg_knowledge": round(avg_k, 2),
                    "avg_skill": round(avg_s, 2),
                    "avg_collab": round(avg_c, 2),
                    "complement_note": note,
                }
            )

        balance_score = self._balance_score(result_groups)
        return {
            "groups": result_groups,
            "balance_score": balance_score,
            "complement_notes": complement_notes,
            "audit_log": audit,
            "config": {"group_size": group_size, "target_sizes": target_sizes, "mode": mode, "priority": priority, "task_requirements": requirements},
        }

    def _add_member(self, group: dict, user: dict):
        group["members"].append(user)
        tech = user.get("tech_skills") or []
        if isinstance(tech, str):
            try:
                tech = json.loads(tech)
            except json.JSONDecodeError:
                tech = []
        group["skills"].update(tech)
        role = user.get("pref_role")
        if role:
            group["roles"].append(role)
        major = user.get("major")
        if major:
            group["majors"].append(major)
        styles = user.get("collab_style") or []
        if isinstance(styles, str):
            try:
                styles = json.loads(styles)
            except json.JSONDecodeError:
                styles = []
        group["styles"].update(styles)
        group["tags"].update(self._tag_names(user))

    def _complement_gain(self, user: dict, group: dict, mode: str) -> float:
        tech = user.get("tech_skills") or []
        if isinstance(tech, str):
            try:
                tech = json.loads(tech)
            except json.JSONDecodeError:
                tech = []
        skill_div = len(set(tech) - group["skills"])
        role_penalty = -2 if user.get("pref_role") in group["roles"] else 0
        major = user.get("major")
        major_penalty = -3 if major and group["majors"].count(major) >= 1 else 0
        styles = user.get("collab_style") or []
        if isinstance(styles, str):
            try:
                styles = json.loads(styles)
            except json.JSONDecodeError:
                styles = []
        style_bonus = sum(1 for s in styles if s not in group["styles"])
        tag_names = self._tag_names(user)
        overlap = len(tag_names & group.get("tags", set()))
        union = len(tag_names | group.get("tags", set())) or 1
        tag_diversity = 1 - overlap / union
        if mode == "skill_focus":
            return skill_div * 0.5 - major_penalty + tag_diversity
        return skill_div + role_penalty + major_penalty + style_bonus + tag_diversity * 2.0

    def _check_balance(self, groups: list, group_size: int) -> bool:
        avgs = []
        for g in groups:
            if not g["members"]:
                continue
            avgs.append(sum(self._score(m, "skill") for m in g["members"]) / len(g["members"]))
        if len(avgs) < 2:
            return True
        if max(avgs) - min(avgs) > Config.BALANCE_SKILL_DIFF:
            return False
        for g in groups:
            majors = g["majors"]
            if any(majors.count(m) > 1 for m in set(majors)):
                return False
        return True

    def _swap_balance(self, groups: list, audit: list):
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if not groups[i]["members"] or not groups[j]["members"]:
                    continue
                a, b = groups[i]["members"][-1], groups[j]["members"][-1]
                groups[i]["members"][-1], groups[j]["members"][-1] = b, a
                audit.append({"swap": [a.get("user_id"), b.get("user_id")]})
                return

    def _balance_score(self, result_groups: list) -> float:
        if not result_groups:
            return 0
        avgs = [g["avg_skill"] for g in result_groups]
        diff = max(avgs) - min(avgs) if avgs else 0
        return round(max(0, 10 - diff * 2), 2)

    def _complement_note(self, g: dict, requirements: dict | None = None) -> str:
        """生成给老师查看的小组说明."""
        members = g.get("members") or []
        roles = list(dict.fromkeys(g.get("roles") or []))
        majors = list(dict.fromkeys(g.get("majors") or []))
        k_avg = sum(self._score(m, "knowledge") for m in members) / max(len(members), 1)
        s_avg = sum(self._score(m, "skill") for m in members) / max(len(members), 1)
        c_avg = sum(self._score(m, "collab") for m in members) / max(len(members), 1)
        req_tags = [t.get("name") if isinstance(t, dict) else str(t) for t in (requirements or {}).get("required_tags") or []]
        req_roles = [str(r) for r in (requirements or {}).get("required_roles") or []]
        matched_tags = sorted(set(req_tags) & set(g.get("tags") or []))
        matched_roles = sorted(set(req_roles) & set(roles))
        parts = [
            f"专业方向覆盖 {len(majors)} 类（{ '、'.join(majors[:3]) or '较多元' }）",
            f"技能标签共 {len(g.get('skills') or [])} 项，组内技能均分 {s_avg:.1f}",
            f"角色方向 {len(roles)} 类（{ '、'.join(roles[:4]) or '待细化' }），协作均分 {c_avg:.1f}",
            f"基础方向均分 {k_avg:.1f}，整体搭配较均衡",
        ]
        if req_tags:
            parts.append(f"任务标签匹配 {len(matched_tags)}/{len(req_tags)}（{ '、'.join(matched_tags[:4]) or '待补充' }）")
        if req_roles:
            parts.append(f"任务角色匹配 {len(matched_roles)}/{len(req_roles)}（{ '、'.join(matched_roles[:4]) or '待补充' }）")
        return "；".join(parts)

    def _score(self, profile: dict, dim: str) -> float:
        return float(profile.get(f"{dim}_final") or profile.get(f"{dim}_score") or 0)

    def _tag_names(self, profile: dict) -> set[str]:
        tags = profile.get("active_tags") or profile.get("passive_tags") or []
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        out = set()
        for tag in tags:
            if isinstance(tag, dict) and tag.get("name"):
                out.add(tag["name"])
            elif isinstance(tag, str):
                out.add(tag)
        return out

    def _task_fit(self, profile: dict, requirements: dict | None) -> float:
        if not requirements:
            return 0.0
        req_tags = {t.get("name") if isinstance(t, dict) else str(t) for t in (requirements.get("required_tags") or [])}
        req_roles = {str(r) for r in (requirements.get("required_roles") or [])}
        tags = self._tag_names(profile)
        tag_score = len(req_tags & tags) * 1.5
        role_score = 2.5 if profile.get("pref_role") in req_roles else 0.0
        goal = str(requirements.get("goal") or "")
        goal_score = sum(1 for tag in tags if tag and tag in goal) * 0.6
        return tag_score + role_score + goal_score

    def validate_manual(self, member_profiles: list[dict], group_size: int) -> dict:
        """手动调整后校验均衡性."""
        groups = [{"members": member_profiles, "skills": set(), "roles": [], "majors": [], "styles": set(), "tags": set()}]
        for m in member_profiles:
            self._add_member({"members": [], "skills": set(), "roles": [], "majors": [], "styles": set(), "tags": set()}, m)
        ok = self._check_balance(
            [{"members": member_profiles, "roles": [m.get("pref_role") for m in member_profiles],
              "majors": [m.get("major") for m in member_profiles], "skills": set(), "tags": set()}],
            group_size,
        )
        avgs = [self._score(m, "skill") for m in member_profiles]
        avg = sum(avgs) / len(avgs) if avgs else 0
        return {"valid": ok, "avg_skill": round(avg, 2), "message": "合规" if ok else "组内同质过高或均衡度不足"}
