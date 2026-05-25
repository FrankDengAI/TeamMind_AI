"""用户模型."""
from datetime import datetime

from app import db


class User(db.Model):
    """系统用户表."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    account = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=True, index=True)
    email_verified_at = db.Column(db.DateTime)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), default="user", nullable=False)  # user | admin
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(16), default="active", nullable=False)  # active | pending | disabled
    token_version = db.Column(db.Integer, default=0, nullable=False)
    last_login_at = db.Column(db.DateTime)
    avatar_url = db.Column(db.String(512))
    bio = db.Column(db.String(240))
    headline = db.Column(db.String(120))
    portfolio_url = db.Column(db.String(512))
    github_url = db.Column(db.String(512))
    research_interest = db.Column(db.String(240))
    availability = db.Column(db.String(120))
    display_theme = db.Column(db.String(32))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = db.relationship("UserProfile", backref="user", uselist=False, lazy=True)
    posts = db.relationship("CommunityPost", backref="user", lazy=True)
    comments = db.relationship("PostComment", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "account": self.account,
            "email": self.email,
            "email_verified": bool(self.email_verified_at),
            "is_demo": bool(self.is_demo),
            "status": self.status,
            "role": self.role,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "headline": self.headline,
            "portfolio_url": self.portfolio_url,
            "github_url": self.github_url,
            "research_interest": self.research_interest,
            "availability": self.availability,
            "display_theme": self.display_theme,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
