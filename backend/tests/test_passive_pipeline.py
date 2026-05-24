"""被动标签流水线测试."""
import json

from app import db
from app.models import CommunityPost, UserProfile
from app.services.passive_tag_pipeline import PassiveTagPipeline


def test_post_like_updates_passive_tags(app):
    with app.app_context():
        prof = UserProfile(user_id=1, knowledge_score=5, skill_score=5, collab_score=5, raw_source="text")
        post = CommunityPost(
            user_id=1,
            content="我在学习 Python 和数据分析，希望找同学合作。",
            tags_json=json.dumps([{"name": "Python", "dimension": "skill", "level": 2}], ensure_ascii=False),
            status="published",
        )
        db.session.add_all([prof, post])
        db.session.commit()

        PassiveTagPipeline().record_post_event(1, post, "post_like")
        db.session.commit()

        updated = UserProfile.query.get(prof.id)
        passive = json.loads(updated.passive_tags_json)
        assert passive[0]["name"] == "Python"
        assert updated.skill_final is not None
