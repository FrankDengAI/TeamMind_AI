"""学习社区、互动与实时聊天相关模型."""
from __future__ import annotations

import json
from datetime import datetime

from app import db


def _loads(value, default=None):
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


class CommunityPost(db.Model):
    __tablename__ = "community_post"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(160), default="")
    content = db.Column(db.Text, nullable=False)
    media_json = db.Column(db.Text)
    tags_json = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(24), default="published", index=True)
    llm_tags_json = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, viewer_id: int | None = None):
        user = getattr(self, "user", None)
        return {
            "id": self.id,
            "user_id": self.user_id if not self.is_anonymous else None,
            "author": "匿名学员" if self.is_anonymous else (user.name if user else f"用户{self.user_id}"),
            "title": self.title,
            "content": self.content,
            "media": _loads(self.media_json),
            "tags": _loads(self.tags_json),
            "is_anonymous": self.is_anonymous,
            "status": self.status,
            "llm_tags": _loads(self.llm_tags_json),
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class PostInteraction(db.Model):
    __tablename__ = "post_interaction"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_post.id"), nullable=False, index=True)
    type = db.Column(db.String(32), nullable=False, index=True)
    meta_json = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "post_id": self.post_id,
            "type": self.type,
            "meta": _loads(self.meta_json, {}),
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class PostComment(db.Model):
    __tablename__ = "post_comment"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_post.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        user = getattr(self, "user", None)
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id if not self.is_anonymous else None,
            "author": "匿名学员" if self.is_anonymous else (user.name if user else f"用户{self.user_id}"),
            "content": self.content,
            "is_anonymous": self.is_anonymous,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class ChatConversation(db.Model):
    __tablename__ = "chat_conversation"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), index=True)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def member_ids(self) -> set[int]:
        if self.group_id:
            from app.models import GroupInfo

            g = GroupInfo.query.get(self.group_id)
            return set(g.member_list()) if g else set()
        return {self.user1_id, self.user2_id}

    def to_dict(self, current_user_id: int | None = None):
        if self.group_id:
            return {
                "id": self.id,
                "group_id": self.group_id,
                "conversation_type": "group",
                "other_user_id": None,
            }
        other_id = self.user2_id if current_user_id == self.user1_id else self.user1_id
        return {
            "id": self.id,
            "user1_id": self.user1_id,
            "user2_id": self.user2_id,
            "group_id": self.group_id,
            "conversation_type": "direct",
            "other_user_id": other_id,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_message"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("chat_conversation.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(24), default="text")
    read_at = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "msg_type": self.msg_type,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
