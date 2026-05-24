"""双标签画像评分测试."""
from app.services.profile_scoring import ProfileScoringEngine


def test_profile_scoring_uses_active_and_llm_tags(app):
    engine = ProfileScoringEngine()
    payload = engine.build_profile_payload(
        active_tags=[
            {"name": "Python", "dimension": "skill", "level": 3},
            {"name": "主动沟通", "dimension": "collab", "level": 2},
        ],
        llm_analysis={
            "knowledge": {"score": 7.0, "degree": "本科", "major": "计算机"},
            "skill": {"score": 8.0},
            "collaboration": {"score": 6.5, "pref_role": "技术开发"},
            "overall_confidence": 0.9,
        },
        rule_result={"knowledge_score": 6, "skill_score": 5, "collab_score": 5, "pref_role": "执行落地"},
        passive_tags=[],
    )

    assert payload["skill_final"] > 5
    assert payload["collab_final"] > 5
    assert payload["pref_role"] == "技术开发"
    assert payload["score_breakdown"]["formula"]["skill"]
