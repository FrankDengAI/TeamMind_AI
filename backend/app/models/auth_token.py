"""邮箱验证码与重置令牌."""
from datetime import datetime

from app import db


class AuthToken(db.Model):
    """邮箱验证码记录（注册 / 重置密码）."""

    __tablename__ = "auth_token"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(128), nullable=False, index=True)
    purpose = db.Column(db.String(32), nullable=False)  # register | reset_password
    code_hash = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
