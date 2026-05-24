"""动态任务调优算法."""
import json
from datetime import datetime
from typing import Any

from app.config import Config


class TaskAdjustAlgorithm:
    """基于行为数据的任务调优."""

    def adjust(
        self,
        tasks: list[dict],
        behavior_summary: dict[int, dict],
        members: list[dict],
    ) -> dict[str, Any]:
        """
        生成调优建议.
        :param behavior_summary: user_id -> {progress, submit_status, active_count, peer_rating, tendency}
        """
        suggestions = []
        warnings = []

        for task in tasks:
            uid = task.get("assignee_id")
            beh = behavior_summary.get(uid, {})
            tendency = beh.get("tendency", "normal")
            progress = beh.get("avg_progress", task.get("progress", 0))

            if tendency == "positive" or progress >= 80:
                suggestions.append(
                    {
                        "task_id": task["id"],
                        "type": "upgrade",
                        "action": "increase_difficulty",
                        "new_difficulty": min(5, task.get("difficulty", 3) + 1),
                        "reason": "表现积极，提升任务难度",
                    }
                )
            elif tendency == "negative" or progress <= 40:
                feedback_part = ""
                if beh.get("feedback_count"):
                    feedback_part = f"，且收到 {beh.get('feedback_count')} 条任务反馈"
                suggestions.append(
                    {
                        "task_id": task["id"],
                        "type": "downgrade",
                        "action": "decrease_difficulty",
                        "new_difficulty": max(1, task.get("difficulty", 3) - 1),
                        "reason": f"进度滞后{feedback_part}，建议降低难度、拆分或安排同伴协助",
                        "feedback_notes": beh.get("feedback_notes", [])[-3:],
                    }
                )
                warnings.append({"user_id": uid, "message": "成员进度预警"})
            else:
                suggestions.append(
                    {
                        "task_id": task["id"],
                        "type": "maintain",
                        "action": "keep",
                        "reason": "维持当前分工",
                    }
                )

        # 负载均衡
        hours = {}
        for t in tasks:
            uid = t.get("assignee_id")
            hours[uid] = hours.get(uid, 0) + t.get("estimated_hours", 2)
        if hours:
            max_h, min_h = max(hours.values()), min(hours.values())
            if max_h - min_h > 4:
                overloaded = max(hours, key=hours.get)
                suggestions.append(
                    {
                        "type": "rebalance",
                        "action": "redistribute",
                        "from_user": overloaded,
                        "reason": "工时负载失衡，建议重新分配",
                    }
                )

        return {
            "suggestions": suggestions,
            "warnings": warnings,
            "adjusted_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def summarize_behavior(logs: list) -> dict[int, dict]:
        """聚合行为日志为每用户摘要."""
        summary = {}
        for log in logs:
            uid = log.user_id if hasattr(log, "user_id") else log.get("user_id")
            if uid not in summary:
                summary[uid] = {
                    "progress_list": [],
                    "submit_statuses": [],
                    "active_count": 0,
                    "peer_ratings": [],
                    "feedback_count": 0,
                    "feedback_notes": [],
                }
            s = summary[uid]
            prog = log.progress if hasattr(log, "progress") else log.get("progress", 0)
            s["progress_list"].append(prog)
            status = log.submit_status if hasattr(log, "submit_status") else log.get("submit_status")
            if status:
                s["submit_statuses"].append(status)
            s["active_count"] += log.active_count if hasattr(log, "active_count") else log.get("active_count", 0)
            pr = log.peer_rating if hasattr(log, "peer_rating") else log.get("peer_rating")
            if pr:
                s["peer_ratings"].append(pr)
            event_type = log.event_type if hasattr(log, "event_type") else log.get("event_type")
            if event_type == "task_feedback":
                s["feedback_count"] += 1
                detail = log.detail if hasattr(log, "detail") else log.get("detail")
                if detail:
                    s["feedback_notes"].append(detail)

        for uid, s in summary.items():
            avg_p = sum(s["progress_list"]) / max(len(s["progress_list"]), 1)
            late = s["submit_statuses"].count("late")
            if s["feedback_count"] >= 2:
                tendency = "negative"
            elif avg_p >= 80 and late == 0:
                tendency = "positive"
            elif avg_p <= 40 or late >= 2 or s["feedback_count"] >= 1:
                tendency = "negative"
            else:
                tendency = "normal"
            s["avg_progress"] = avg_p
            s["tendency"] = tendency
        return summary

    def apply_suggestion(self, task, suggestion: dict) -> None:
        """将确认的建议应用到任务."""
        if suggestion.get("action") == "increase_difficulty":
            task.difficulty = suggestion.get("new_difficulty", task.difficulty)
        elif suggestion.get("action") == "decrease_difficulty":
            task.difficulty = suggestion.get("new_difficulty", task.difficulty)
        task.adjust_times = (task.adjust_times or 0) + 1
        hist = []
        if task.adjust_history:
            try:
                hist = json.loads(task.adjust_history)
            except json.JSONDecodeError:
                pass
        hist.append({"suggestion": suggestion, "applied_at": datetime.utcnow().isoformat()})
        if len(hist) > Config.MAX_ADJUST_HISTORY:
            hist = hist[-Config.MAX_ADJUST_HISTORY :]
        task.adjust_history = json.dumps(hist, ensure_ascii=False)
        task.pending_adjust = None
