"""任务分配测试."""
from app.services.algorithms.task_assign import TaskAssignAlgorithm


def test_assign_tasks():
    algo = TaskAssignAlgorithm()
    members = [
        {"user_id": 1, "skill_score": 8, "pref_role": "技术开发"},
        {"user_id": 2, "skill_score": 6, "pref_role": "设计执行"},
        {"user_id": 3, "skill_score": 7, "pref_role": "数据支持"},
        {"user_id": 4, "skill_score": 5, "pref_role": "协调对接"},
    ]
    tasks = algo.assign(1, members, "product_dev")
    assert len(tasks) >= 4
    assignees = [t["assignee_id"] for t in tasks]
    assert len(set(assignees)) >= 2
