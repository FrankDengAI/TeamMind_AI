"""活动/小组里程碑."""
from datetime import datetime

from app import db


class Milestone(db.Model):
    __tablename__ = "milestone"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("team_activity.id"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), index=True)
    title = db.Column(db.String(120), nullable=False)
    due_at = db.Column(db.DateTime)
    status = db.Column(db.String(24), default="pending")
    sort_order = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "group_id": self.group_id,
            "title": self.title,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "status": self.status,
            "sort_order": self.sort_order or 0,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
