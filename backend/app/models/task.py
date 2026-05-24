"""任务模型."""
import json
from datetime import datetime

from app import db


class Task(db.Model):
    """任务表."""

    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=3)  # 1-5
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), index=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    role_required = db.Column(db.String(64))
    estimated_hours = db.Column(db.Float, default=2.0)
    depends_on = db.Column(db.Text)  # JSON list task ids
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(32), default="pending")  # pending|in_progress|done|blocked
    progress = db.Column(db.Integer, default=0)
    adjust_times = db.Column(db.Integer, default=0)
    adjust_history = db.Column(db.Text)  # JSON version chain
    pending_adjust = db.Column(db.Text)  # 待确认调优建议
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        hist = []
        pending = None
        deps = []
        if self.adjust_history:
            try:
                hist = json.loads(self.adjust_history)
            except json.JSONDecodeError:
                pass
        if self.pending_adjust:
            try:
                pending = json.loads(self.pending_adjust)
            except json.JSONDecodeError:
                pass
        if self.depends_on:
            try:
                deps = json.loads(self.depends_on)
            except json.JSONDecodeError:
                pass
        assign_reason = ""
        if self.description and "【分配依据】" in self.description:
            assign_reason = self.description.split("【分配依据】", 1)[-1].strip()

        return {
            "id": self.id,
            "task_name": self.task_name,
            "description": self.description,
            "assign_reason": assign_reason,
            "difficulty": self.difficulty,
            "group_id": self.group_id,
            "assignee_id": self.assignee_id,
            "role_required": self.role_required,
            "estimated_hours": self.estimated_hours,
            "depends_on": deps,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status,
            "progress": self.progress,
            "adjust_times": self.adjust_times,
            "adjust_history": hist,
            "pending_adjust": pending,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
