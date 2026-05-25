"""异构智能分组算法 - 贪心 + 均衡微调，支持多模板模式."""
import json
import math
import random
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
        constraints: dict | None = None,
    ) -> dict[str, Any]:
        """
        执行分组.
        :param profiles: 含 user_id, skill_score, knowledge_score, collab_score 等
        :param constraints: 来自分组模板，如 min_roles_per_group、max_same_major_ratio
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
        constraints = constraints or {}
        mode = (mode or "heterogeneous").lower()
        if mode == "task_auto":
            mode = "heterogeneous"

        groups: list[dict] = [
            {"members": [], "skills": set(), "roles": [], "majors": [], "styles": set(), "tags": set()}
            for _ in range(num_groups)
        ]

        if mode == "homogeneous":
            self._fill_homogeneous(profiles, groups, target_sizes)
        elif mode == "random":
            self._fill_random(profiles, groups, target_sizes)
        else:
            self._fill_heterogeneous(profiles, groups, target_sizes, mode, priority, requirements, constraints)

        audit = []
        for _ in range(20):
            if self._check_balance(groups, group_size, constraints):
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
        skill_spread = self._within_group_skill_spread(result_groups)
        return {
            "groups": result_groups,
            "balance_score": balance_score,
            "skill_spread_within_groups": skill_spread,
            "complement_notes": complement_notes,
            "audit_log": audit,
            "config": {
                "group_size": group_size,
                "target_sizes": target_sizes,
                "mode": mode,
                "priority": priority,
                "task_requirements": requirements,
                "constraints": constraints,
            },
        }

    def _fill_heterogeneous(
        self,
        profiles: list[dict],
        groups: list[dict],
        target_sizes: list[int],
        mode: str,
        priority: str,
        requirements: dict,
        constraints: dict,
    ) -> None:
        sorted_profiles = sorted(
            profiles,
            key=lambda p: self._score(p, "skill") + self._task_fit(p, requirements),
            reverse=True,
        )
        num_groups = len(groups)
        seeds = sorted_profiles[:num_groups]
        rest = sorted_profiles[num_groups:]
        for i, seed in enumerate(seeds):
            self._add_member(groups[i], seed)
        for user in rest:
            best_gi = None
            best_gain = -999
            for gi, g in enumerate(groups):
                if len(g["members"]) >= target_sizes[gi]:
                    continue
                gain = self._complement_gain(user, g, mode, priority, constraints, target_sizes[gi])
                if gain > best_gain:
                    best_gain = gain
                    best_gi = gi
            if best_gi is None:
                best_gi = min(range(len(groups)), key=lambda gi: len(groups[gi]["members"]))
            self._add_member(groups[best_gi], user)

    def _fill_homogeneous(self, profiles: list[dict], groups: list[dict], target_sizes: list[int]) -> None:
        """按技能排序后连续切块，使组内能力相近."""
        sorted_profiles = sorted(profiles, key=lambda p: self._score(p, "skill"), reverse=True)
        idx = 0
        for gi, size in enumerate(target_sizes):
            chunk = sorted_profiles[idx : idx + size]
            idx += size
            for user in chunk:
                self._add_member(groups[gi], user)

    def _fill_random(self, profiles: list[dict], groups: list[dict], target_sizes: list[int]) -> None:
        shuffled = list(profiles)
        random.shuffle(shuffled)
        idx = 0
        for gi, size in enumerate(target_sizes):
            for user in shuffled[idx : idx + size]:
                self._add_member(groups[gi], user)
            idx += size

    def _add_member(self, group: dict, user: dict):
        group["members"].append(user)
        tech = user.get("tech_skills") or []
        if isinstance(tech, str):
            try:
                tech = json.loads(tech)
            except json.JSONDecodeError:
                tech = []
        group["skills"].update(tech if isinstance(tech, list) else [])
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
        group["styles"].update(styles if isinstance(styles, list) else [])
        group["tags"].update(self._tag_names(user))

    def _complement_gain(
        self,
        user: dict,
        group: dict,
        mode: str,
        priority: str,
        constraints: dict,
        group_capacity: int,
    ) -> float:
        tech = user.get("tech_skills") or []
        if isinstance(tech, str):
            try:
                tech = json.loads(tech)
            except json.JSONDecodeError:
                tech = []
        skill_div = len(set(tech) - group["skills"])
        role = user.get("pref_role")
        role_penalty = -2 if role and role in group["roles"] else 0
        role_bonus = 3 if role and role not in group["roles"] and len(set(group["roles"])) < constraints.get("min_roles_per_group", 0) else 0
        major = user.get("major")
        major_penalty = 0
        if major and group["majors"]:
            same = group["majors"].count(major)
            max_same = max(1, int((constraints.get("max_same_major_ratio") or 1) * max(group_capacity, 1)))
            if same >= max_same:
                major_penalty = -8
            elif same >= 1:
                major_penalty = -3
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

        if mode == "homogeneous":
            skill_gap = abs(self._score(user, "skill") - (
                sum(self._score(m, "skill") for m in group["members"]) / max(len(group["members"]), 1)
            ))
            return -skill_gap * 2 + skill_div

        if priority == "role":
            return role_bonus + role_penalty * 2 + major_penalty + tag_diversity
        if priority == "major":
            return -major_penalty * 2 + tag_diversity + skill_div * 0.3
        if mode == "skill_focus":
            return skill_div * 0.5 - major_penalty + tag_diversity
        return skill_div + role_penalty + role_bonus + major_penalty + style_bonus + tag_diversity * 2.0

    def _check_balance(self, groups: list, group_size: int, constraints: dict) -> bool:
        avgs = []
        for g in groups:
            if not g["members"]:
                continue
            avgs.append(sum(self._score(m, "skill") for m in g["members"]) / len(g["members"]))
        if len(avgs) >= 2 and max(avgs) - min(avgs) > Config.BALANCE_SKILL_DIFF:
            return False
        min_roles = int(constraints.get("min_roles_per_group") or 0)
        for g in groups:
            if min_roles and len(set(g["roles"])) < min_roles and len(g["members"]) >= group_size:
                return False
            majors = g["majors"]
            if any(majors.count(m) > 1 for m in set(majors)):
                max_ratio = constraints.get("max_same_major_ratio")
                if max_ratio is not None and max_ratio < 1:
                    for m in set(majors):
                        if majors.count(m) > max(1, int(max_ratio * len(g["members"]))):
                            return False
        return True

    def _swap_balance(self, groups: list, audit: list):
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if not groups[i]["members"] or not groups[j]["members"]:
                    continue
                a, b = groups[i]["members"][-1], groups[j]["members"][-1]
                groups[i]["members"][-1], groups[j]["members"][-1] = b, a
                self._rebuild_group_meta(groups[i])
                self._rebuild_group_meta(groups[j])
                audit.append({"swap": [a.get("user_id"), b.get("user_id")]})
                return

    def _rebuild_group_meta(self, group: dict):
        group["skills"] = set()
        group["roles"] = []
        group["majors"] = []
        group["styles"] = set()
        group["tags"] = set()
        members = list(group["members"])
        group["members"] = []
        for m in members:
            self._add_member(group, m)

    def _balance_score(self, result_groups: list) -> float:
        if not result_groups:
            return 0
        avgs = [g["avg_skill"] for g in result_groups]
        diff = max(avgs) - min(avgs) if avgs else 0
        return round(max(0, 10 - diff * 2), 2)

    def _within_group_skill_spread(self, result_groups: list) -> list[float]:
        spreads = []
        for g in result_groups:
            members = g.get("members") or []
            if len(members) < 2:
                spreads.append(0.0)
                continue
            skills = [self._score(m, "skill") for m in members]
            spreads.append(round(max(skills) - min(skills), 2))
        return spreads

    def _complement_note(self, g: dict, requirements: dict | None = None) -> str:
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
            f"专业方向覆盖 {len(majors)} 类（{'、'.join(majors[:3]) or '较多元'}）",
            f"技能标签共 {len(g.get('skills') or [])} 项，组内技能均分 {s_avg:.1f}",
            f"角色方向 {len(roles)} 类（{'、'.join(roles[:4]) or '待细化'}），协作均分 {c_avg:.1f}",
            f"基础方向均分 {k_avg:.1f}，整体搭配较均衡",
        ]
        if req_tags:
            parts.append(f"任务标签匹配 {len(matched_tags)}/{len(req_tags)}（{'、'.join(matched_tags[:4]) or '待补充'}）")
        if req_roles:
            parts.append(f"任务角色匹配 {len(matched_roles)}/{len(req_roles)}（{'、'.join(matched_roles[:4]) or '待补充'}）")
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
        groups = [
            {
                "members": list(member_profiles),
                "skills": set(),
                "roles": [],
                "majors": [],
                "styles": set(),
                "tags": set(),
            }
        ]
        self._rebuild_group_meta(groups[0])
        ok = self._check_balance(groups, group_size, {})
        avgs = [self._score(m, "skill") for m in member_profiles]
        avg = sum(avgs) / len(avgs) if avgs else 0
        return {"valid": ok, "avg_skill": round(avg, 2), "message": "合规" if ok else "组内同质过高或均衡度不足"}
