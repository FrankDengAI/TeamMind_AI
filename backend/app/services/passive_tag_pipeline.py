"""基于社区互动、聊天和任务行为的被动标签更新."""
from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any

from app import db
from app.models import ChatConversation, ChatMessage, CommunityPost, PostInteraction, UserProfile
from app.services.profile_scoring import ProfileScoringEngine
from app.services.tag_catalog import normalize_active_tags, tag_by_name


EVENT_STRENGTH = {
    "post_view": 0.10,
    "post_view_deep": 0.25,
    "post_like": 0.35,
    "post_favorite": 0.60,
    "post_comment": 0.50,
    "profile_view": 0.20,
    "chat_open": 0.30,
    "chat_message": 0.40,
    "task_peer_rating": 0.70,
}
DECAY_LAMBDA = 0.05


class PassiveTagPipeline:
    """把行为事件转换为用户被动标签，并重算画像."""

    def record_post_event(self, user_id: int, post: CommunityPost, event_type: str, meta: dict | None = None) -> None:
        db.session.add(
            PostInteraction(
                user_id=user_id,
                post_id=post.id,
                type=event_type,
                meta_json=json.dumps(meta or {}, ensure_ascii=False),
            )
        )
        self.apply_tags_from_content(
            user_id=user_id,
            tags=_safe_json(post.tags_json),
            event_type=event_type,
            anonymous=bool(post.is_anonymous),
        )

    def record_chat_event(self, sender_id: int, conversation_id: int) -> None:
        conv = ChatConversation.query.get(conversation_id)
        if not conv:
            return
        other_id = conv.user2_id if sender_id == conv.user1_id else conv.user1_id
        other_profile = UserProfile.query.filter_by(user_id=other_id).order_by(UserProfile.create_time.desc()).first()
        other_tags = _safe_json(other_profile.active_tags_json) if other_profile else []
        if not other_tags:
            return
        count = ChatMessage.query.filter_by(conversation_id=conversation_id).count()
        if count < 5:
            self.apply_tags_from_content(sender_id, other_tags[:3], "chat_message", anonymous=False, multiplier=0.3)
            return
        affinity = min(1.0, 0.2 + 0.1 * min(count // 5, 5))
        self.apply_tags_from_content(sender_id, other_tags[:5], "chat_message", anonymous=False, multiplier=0.15 * affinity)

    def apply_tags_from_content(
        self,
        user_id: int,
        tags: list[dict] | list[str],
        event_type: str,
        anonymous: bool = False,
        multiplier: float = 1.0,
    ) -> None:
        profile = UserProfile.query.filter_by(user_id=user_id).order_by(UserProfile.create_time.desc()).first()
        if not profile:
            return
        normalized = normalize_active_tags(tags)
        if not normalized:
            return
        current = _safe_json(profile.passive_tags_json)
        by_name = {t.get("name"): t for t in current if t.get("name")}
        base = EVENT_STRENGTH.get(event_type, 0.2)
        anon = 0.7 if anonymous else 1.0
        now = datetime.utcnow()
        catalog = tag_by_name()
        for tag in normalized:
            name = tag.get("name")
            old = by_name.get(name, {"name": name, "weight": 0, "weights": tag.get("weights") or catalog.get(name, {}).get("weights", {})})
            days = 0
            if old.get("updated_at"):
                try:
                    days = max(0, (now - datetime.fromisoformat(old["updated_at"])).days)
                except ValueError:
                    days = 0
            delta = base * anon * multiplier * math.exp(-DECAY_LAMBDA * days)
            old["weight"] = round(min(1.0, float(old.get("weight") or 0) + delta), 3)
            old["source"] = event_type
            old["updated_at"] = now.isoformat()
            old["weights"] = old.get("weights") or tag.get("weights") or catalog.get(name, {}).get("weights", {})
            by_name[name] = old
        profile.passive_tags_json = json.dumps(sorted(by_name.values(), key=lambda x: x.get("weight", 0), reverse=True)[:30], ensure_ascii=False)
        self.recalculate_profile(profile)

    def recalculate_profile(self, profile: UserProfile) -> None:
        engine = ProfileScoringEngine()
        payload = engine.build_profile_payload(
            active_tags=_safe_json(profile.active_tags_json),
            llm_analysis=_safe_json(profile.llm_analysis_json, {}),
            rule_result=profile.to_dict(),
            passive_tags=_safe_json(profile.passive_tags_json),
            user_id=profile.user_id,
        )
        profile.knowledge_score = payload["knowledge_score"]
        profile.skill_score = payload["skill_score"]
        profile.collab_score = payload["collab_score"]
        profile.knowledge_final = payload["knowledge_final"]
        profile.skill_final = payload["skill_final"]
        profile.collab_final = payload["collab_final"]
        profile.score_breakdown_json = json.dumps(payload["score_breakdown"], ensure_ascii=False)
        db.session.commit()


def _safe_json(value: Any, default=None):
    if default is None:
        default = []
    if not value:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
