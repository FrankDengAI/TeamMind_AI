"""分组算法测试."""
from app.services.algorithms.grouping import GroupingAlgorithm


def _mock_profiles(n=12):
    profiles = []
    majors = ["计算机", "金融", "设计", "市场", "机械"]
    roles = ["技术开发", "设计执行", "数据支持", "创意策划", "协调对接"]
    for i in range(n):
        profiles.append(
            {
                "user_id": i + 1,
                "skill_score": 5 + (i % 5),
                "knowledge_score": 6,
                "collab_score": 7,
                "major": majors[i % len(majors)],
                "pref_role": roles[i % len(roles)],
                "tech_skills": [f"skill_{i % 3}", f"skill_{(i+1) % 3}"],
                "collab_style": ["积极主动"],
            }
        )
    return profiles


def test_create_groups_balance():
    algo = GroupingAlgorithm()
    result = algo.create_groups(_mock_profiles(), group_size=4)
    assert len(result["groups"]) == 3
    assert result["balance_score"] >= 0
    avgs = [g["avg_skill"] for g in result["groups"]]
    assert max(avgs) - min(avgs) <= 3
