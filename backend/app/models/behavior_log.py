"""协作行为日志模型."""
from datetime import datetime

from app import db


class BehaviorLog(db.Model):
    """行为埋点表."""

    __tablename__ = "behavior_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), index=True)
    group_id = db.Column(db.Integer, index=True)
    progress = db.Column(db.Integer, default=0)
    submit_status = db.Column(db.String(16))  # early|on_time|late|none
    active_count = db.Column(db.Integer, default=0)
    collab_score = db.Column(db.Float)
    comment_count = db.Column(db.Integer, default=0)
    peer_rating = db.Column(db.Float)
    tendency = db.Column(db.String(32))  # positive|normal|negative
    event_type = db.Column(db.String(32), default="progress", index=True)
    detail = db.Column(db.Text)
    record_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "group_id": self.group_id,
            "progress": self.progress,
            "submit_status": self.submit_status,
            "active_count": self.active_count,
            "collab_score": self.collab_score,
            "comment_count": self.comment_count,
            "peer_rating": self.peer_rating,
            "tendency": self.tendency,
            "event_type": self.event_type,
            "detail": self.detail,
            "record_time": self.record_time.isoformat() if self.record_time else None,
        }
