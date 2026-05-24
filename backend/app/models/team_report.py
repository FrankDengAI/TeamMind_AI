"""团队质量报告模型."""
from datetime import datetime

from app import db


class TeamReport(db.Model):
    """团队协作报告表."""

    __tablename__ = "team_report"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), nullable=False, index=True)
    completion_rate = db.Column(db.Float, default=0)
    balance_score = db.Column(db.Float, default=0)
    quality_score = db.Column(db.Float, default=0)
    risk_level = db.Column(db.String(16), default="low")  # low|medium|high
    detail = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "completion_rate": self.completion_rate,
            "balance_score": self.balance_score,
            "quality_score": self.quality_score,
            "risk_level": self.risk_level,
            "detail": self.detail,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
