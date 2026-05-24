"""分组信息模型."""
import json
from datetime import datetime

from app import db


class GroupInfo(db.Model):
    """小组信息表."""

    __tablename__ = "group_info"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("team_activity.id"), index=True)
    group_name = db.Column(db.String(128), nullable=False)
    member_ids = db.Column(db.Text, nullable=False)  # JSON list[int]
    avg_knowledge = db.Column(db.Float, default=0)
    avg_skill = db.Column(db.Float, default=0)
    avg_collab = db.Column(db.Float, default=0)
    balance_score = db.Column(db.Float, default=0)
    config = db.Column(db.Text)  # 分组参数与审计日志 JSON
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def member_list(self):
        try:
            return json.loads(self.member_ids or "[]")
        except json.JSONDecodeError:
            return []

    def to_dict(self):
        cfg = {}
        if self.config:
            try:
                cfg = json.loads(self.config)
            except json.JSONDecodeError:
                pass
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "group_name": self.group_name,
            "member_ids": self.member_list(),
            "avg_knowledge": self.avg_knowledge,
            "avg_skill": self.avg_skill,
            "avg_collab": self.avg_collab,
            "balance_score": self.balance_score,
            "config": cfg,
            "member_roles": cfg.get("member_roles") or [],
            "complement_note": cfg.get("complement_note") or "",
            "ai_analysis": cfg.get("ai_analysis") or None,
            "grouping_mode": cfg.get("mode", "heterogeneous"),
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
