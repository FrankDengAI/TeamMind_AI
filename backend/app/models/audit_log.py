"""操作审计日志模型."""
from datetime import datetime

from app import db


class AuditLog(db.Model):
    """审计日志表 - 记录关键操作."""

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, index=True)
    action = db.Column(db.String(64), nullable=False)
    resource = db.Column(db.String(64))
    resource_id = db.Column(db.Integer)
    detail = db.Column(db.Text)
    ip = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "detail": self.detail,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
