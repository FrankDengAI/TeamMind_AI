"""实时聊天 REST 与 Socket.IO 事件."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import decode_token, get_jwt_identity, jwt_required
from sqlalchemy import or_

from app import db, socketio
from app.models import ChatConversation, ChatMessage, User
from app.services.passive_tag_pipeline import PassiveTagPipeline
from app.middleware.auth import get_request_user_id

bp = Blueprint("chat", __name__)
pipeline = PassiveTagPipeline()


@bp.route("/conversations", methods=["GET"])
@jwt_required()
def conversations():
    uid = get_request_user_id()
    convs = ChatConversation.query.filter(or_(ChatConversation.user1_id == uid, ChatConversation.user2_id == uid)).order_by(
        ChatConversation.last_message_at.desc()
    ).all()
    data = []
    for conv in convs:
        item = conv.to_dict(uid)
        other = User.query.get(item["other_user_id"])
        last = ChatMessage.query.filter_by(conversation_id=conv.id).order_by(ChatMessage.create_time.desc()).first()
        item["other_user"] = other.to_dict() if other else None
        item["last_message"] = last.to_dict() if last else None
        item["unread"] = ChatMessage.query.filter(
            ChatMessage.conversation_id == conv.id,
            ChatMessage.sender_id != uid,
            ChatMessage.read_at.is_(None),
        ).count()
        data.append(item)
    return jsonify(data)


@bp.route("/conversations", methods=["POST"])
@jwt_required()
def create_conversation():
    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    target = int(data.get("target_user_id") or 0)
    if not target or target == uid:
        return jsonify({"error": "target_user_id 无效"}), 400
    if not User.query.get(target):
        return jsonify({"error": "目标用户不存在"}), 404
    conv = _get_or_create_conversation(uid, target)
    return jsonify(conv.to_dict(uid))


@bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@jwt_required()
def messages(conversation_id):
    uid = get_request_user_id()
    conv = ChatConversation.query.get_or_404(conversation_id)
    if uid not in conv.member_ids():
        return jsonify({"error": "无权访问"}), 403
    rows = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.create_time.asc()).limit(200).all()
    return jsonify([m.to_dict() for m in rows])


@bp.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
@jwt_required()
def send_message_rest(conversation_id):
    uid = get_request_user_id()
    conv = ChatConversation.query.get_or_404(conversation_id)
    if uid not in conv.member_ids():
        return jsonify({"error": "无权访问"}), 403
    data = request.get_json(silent=True) or {}
    try:
        msg = _save_message(conv, uid, data.get("content") or "", data.get("msg_type") or "text")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(msg.to_dict()), 201


@bp.route("/conversations/<int:conversation_id>/read", methods=["POST"])
@jwt_required()
def mark_read(conversation_id):
    uid = get_request_user_id()
    conv = ChatConversation.query.get_or_404(conversation_id)
    if uid not in conv.member_ids():
        return jsonify({"error": "无权访问"}), 403
    ChatMessage.query.filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.sender_id != uid,
        ChatMessage.read_at.is_(None),
    ).update({"read_at": datetime.utcnow()})
    db.session.commit()
    return jsonify({"ok": True})


def _get_or_create_conversation(uid: int, target: int) -> ChatConversation:
    a, b = sorted([uid, target])
    conv = ChatConversation.query.filter_by(user1_id=a, user2_id=b).first()
    if conv:
        return conv
    conv = ChatConversation(user1_id=a, user2_id=b)
    db.session.add(conv)
    db.session.commit()
    return conv


def _save_message(conv: ChatConversation, sender_id: int, content: str, msg_type: str = "text") -> ChatMessage:
    content = (content or "").strip()
    if not content:
        raise ValueError("消息不能为空")
    msg = ChatMessage(conversation_id=conv.id, sender_id=sender_id, content=content[:2000], msg_type=msg_type)
    conv.last_message_at = datetime.utcnow()
    db.session.add(msg)
    db.session.commit()
    pipeline.record_chat_event(sender_id, conv.id)
    db.session.commit()
    return msg


if socketio is not None:

    @socketio.on("connect")
    def socket_connect(auth=None):  # pragma: no cover - socket smoke tested manually
        token = (auth or {}).get("token") or request.args.get("token")
        if not token:
            return False
        try:
            decode_token(token)
            return True
        except Exception:
            return False

    @socketio.on("send_message")
    def socket_send_message(data):  # pragma: no cover
        try:
            uid = int(decode_token(data.get("token"))["sub"])
            target = int(data.get("target_user_id") or 0)
            conv_id = data.get("conversation_id")
            conv = ChatConversation.query.get(conv_id) if conv_id else _get_or_create_conversation(uid, target)
            if uid not in conv.member_ids():
                return {"error": "无权访问"}
            msg = _save_message(conv, uid, data.get("content") or "", data.get("msg_type") or "text")
            socketio.emit("message", msg.to_dict(), room=f"user:{conv.user1_id}")
            socketio.emit("message", msg.to_dict(), room=f"user:{conv.user2_id}")
            return msg.to_dict()
        except Exception as exc:
            return {"error": str(exc)}
