"""主动标签、LLM 解析、被动行为与任务表现融合评分."""
from __future__ import annotations

from statistics import mean
from typing import Any

from app.models import BehaviorLog
from app.services.tag_catalog import normalize_active_tags, tag_by_name


LEVEL_FACTOR = {1: 0.6, 2: 0.85, 3: 1.0}
DIMENSIONS = ("knowledge", "skill", "collab")


def clamp_score(v: float) -> float:
    return round(max(0.0, min(10.0, float(v or 0))), 1)


class ProfileScoringEngine:
    """三维画像综合评分引擎."""

    def build_profile_payload(
        self,
        *,
        active_tags: Any,
        llm_analysis: dict | None,
        rule_result: dict | None,
        passive_tags: list[dict] | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        active = normalize_active_tags(active_tags)
        passive = passive_tags or []
        active_scores = self._score_tags(active)
        llm_scores = self._score_llm(llm_analysis or {})
        passive_scores = self._score_passive(passive)
        task_scores = self._score_task(user_id) if user_id else {"knowledge": 5, "skill": 5, "collab": 5}
        rule_scores = self._score_rule(rule_result or {})

        finals = {
            "knowledge": clamp_score(
                active_scores["knowledge"] * 0.30
                + llm_scores["knowledge"] * 0.30
                + passive_scores["knowledge"] * 0.15
                + task_scores["knowledge"] * 0.15
                + rule_scores["knowledge"] * 0.10
            ),
            "skill": clamp_score(
                active_scores["skill"] * 0.35
                + llm_scores["skill"] * 0.30
                + passive_scores["skill"] * 0.15
                + task_scores["skill"] * 0.20
            ),
            "collab": clamp_score(
                active_scores["collab"] * 0.25
                + llm_scores["collab"] * 0.20
                + passive_scores["collab"] * 0.30
                + task_scores["collab"] * 0.25
            ),
        }

        breakdown = {
            "active": active_scores,
            "llm": llm_scores,
            "passive": passive_scores,
            "task": task_scores,
            "rule": rule_scores,
            "formula": {
                "knowledge": "0.30*active + 0.30*llm + 0.15*passive + 0.15*task + 0.10*rule",
                "skill": "0.35*active + 0.30*llm + 0.15*passive + 0.20*task",
                "collab": "0.25*active + 0.20*llm + 0.30*passive + 0.25*task",
            },
        }

        return {
            "active_tags": active,
            "passive_tags": passive,
            "llm_analysis": llm_analysis or {},
            "score_breakdown": breakdown,
            "knowledge_score": finals["knowledge"],
            "skill_score": finals["skill"],
            "collab_score": finals["collab"],
            "knowledge_final": finals["knowledge"],
            "skill_final": finals["skill"],
            "collab_final": finals["collab"],
            "pref_role": self._pref_role(active, llm_analysis, rule_result),
            "degree": self._pick(llm_analysis, "knowledge", "degree") or (rule_result or {}).get("degree"),
            "major": self._pick(llm_analysis, "knowledge", "major") or (rule_result or {}).get("major"),
        }

    def _score_tags(self, tags: list[dict]) -> dict[str, float]:
        if not tags:
            return {"knowledge": 5.0, "skill": 5.0, "collab": 5.0}
        totals = {d: 0.0 for d in DIMENSIONS}
        weights = {d: 0.0 for d in DIMENSIONS}
        for tag in tags:
            level = LEVEL_FACTOR.get(int(tag.get("level") or 2), 0.85)
            tag_weights = tag.get("weights") or {}
            for dim in DIMENSIONS:
                w = float(tag_weights.get(dim) or 0)
                if w <= 0:
                    continue
                totals[dim] += w * level
                weights[dim] += max(w, 0.1)
        return {dim: clamp_score(10 * totals[dim] / max(weights[dim], 1.0)) for dim in DIMENSIONS}

    def _score_llm(self, analysis: dict) -> dict[str, float]:
        conf = float(analysis.get("overall_confidence") or 0.75)
        return {
            "knowledge": clamp_score(float((analysis.get("knowledge") or {}).get("score") or 5) * conf + 5 * (1 - conf)),
            "skill": clamp_score(float((analysis.get("skill") or {}).get("score") or 5) * conf + 5 * (1 - conf)),
            "collab": clamp_score(float((analysis.get("collaboration") or {}).get("score") or 5) * conf + 5 * (1 - conf)),
        }

    def _score_passive(self, tags: list[dict]) -> dict[str, float]:
        if not tags:
            return {"knowledge": 5.0, "skill": 5.0, "collab": 5.0}
        by_name = tag_by_name()
        totals = {d: 0.0 for d in DIMENSIONS}
        weights = {d: 0.0 for d in DIMENSIONS}
        for tag in tags:
            name = tag.get("name")
            strength = float(tag.get("weight") or tag.get("strength") or 0)
            tag_weights = tag.get("weights") or by_name.get(name, {}).get("weights") or {}
            for dim in DIMENSIONS:
                w = float(tag_weights.get(dim) or 0)
                totals[dim] += strength * w
                weights[dim] += strength
        return {dim: clamp_score(10 * totals[dim] / max(weights[dim], 1.0)) for dim in DIMENSIONS}

    def _score_task(self, user_id: int) -> dict[str, float]:
        logs = BehaviorLog.query.filter_by(user_id=user_id).order_by(BehaviorLog.record_time.desc()).limit(30).all()
        if not logs:
            return {"knowledge": 5.0, "skill": 5.0, "collab": 5.0}
        progress = mean([float(l.progress or 0) for l in logs]) / 10
        peer = [float(l.peer_rating) for l in logs if l.peer_rating is not None]
        peer_score = mean(peer) * 2 if peer else 5
        active = min(10, mean([float(l.active_count or 0) for l in logs]) * 2 + mean([float(l.comment_count or 0) for l in logs]))
        skill = clamp_score(progress * 0.6 + peer_score * 0.4)
        collab = clamp_score(active * 0.5 + peer_score * 0.5)
        return {"knowledge": clamp_score(skill * 0.8), "skill": skill, "collab": collab}

    def _score_rule(self, rule: dict) -> dict[str, float]:
        return {
            "knowledge": clamp_score(rule.get("knowledge_score", 5)),
            "skill": clamp_score(rule.get("skill_score", 5)),
            "collab": clamp_score(rule.get("collab_score", 5)),
        }

    def _pref_role(self, active: list[dict], llm: dict | None, rule: dict | None) -> str:
        for tag in active:
            if tag.get("category") == "偏好角色":
                return tag.get("name") or "执行落地"
        role = ((llm or {}).get("collaboration") or {}).get("pref_role")
        return role or (rule or {}).get("pref_role") or "执行落地"

    def _pick(self, analysis: dict | None, section: str, key: str):
        return ((analysis or {}).get(section) or {}).get(key)
