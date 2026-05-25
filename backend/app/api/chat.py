"""???? REST ? Socket.IO ??."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.middleware.auth import jwt_required_compat
from sqlalchemy import or_

from app import db, socketio
from app.models import ChatConversation, ChatMessage, User
from app.services.passive_tag_pipeline import PassiveTagPipeline
from app.middleware.auth import decode_jwt_token, get_request_user_id
from app.services.class_membership import users_share_active_class

bp = Blueprint("chat", __name__)
pipeline = PassiveTagPipeline()


def _group_conversations_for_user(uid: int) -> list[ChatConversation]:
    from app.models import GroupInfo

    groups = GroupInfo.query.all()
    out = []
    for g in groups:
        if uid not in g.member_list():
            continue
        conv = ChatConversation.query.filter_by(group_id=g.id).first()
        if not conv:
            conv = ChatConversation(group_id=g.id, last_message_at=datetime.utcnow())
            db.session.add(conv)
            db.session.commit()
        out.append(conv)
    return out


@bp.route("/groups/<int:group_id>/conversation", methods=["GET"])
@jwt_required_compat
def group_conversation(group_id):
    from app.models import GroupInfo

    uid = get_request_user_id()
    g = GroupInfo.query.get_or_404(group_id)
    if uid not in g.member_list():
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "????????"}), 403
    conv = ChatConversation.query.filter_by(group_id=group_id).first()
    if not conv:
        conv = ChatConversation(group_id=group_id, last_message_at=datetime.utcnow())
        db.session.add(conv)
        db.session.commit()
    return jsonify(conv.to_dict(uid))


@bp.route("/conversations", methods=["GET"])
@jwt_required_compat
def conversations():
    uid = get_request_user_id()
    direct = ChatConversation.query.filter(
        or_(ChatConversation.user1_id == uid, ChatConversation.user2_id == uid),
        ChatConversation.group_id.is_(None),
    ).order_by(ChatConversation.last_message_at.desc()).all()
    group_convs = _group_conversations_for_user(uid)
    convs = list(direct) + group_convs
    convs.sort(key=lambda c: c.last_message_at or datetime.min, reverse=True)
    data = []
    for conv in convs:
        item = conv.to_dict(uid)
        if conv.group_id:
            from app.models import GroupInfo

            g = GroupInfo.query.get(conv.group_id)
            item["group"] = {"id": conv.group_id, "group_name": g.group_name if g else ""}
            item["title"] = g.group_name if g else f"?? #{conv.group_id}"
        else:
            other = User.query.get(item.get("other_user_id"))
            item["other_user"] = other.to_dict() if other else None
            item["title"] = other.name if other else ""
        last = ChatMessage.query.filter_by(conversation_id=conv.id).order_by(ChatMessage.create_time.desc()).first()
        item["last_message"] = last.to_dict() if last else None
        item["unread"] = ChatMessage.query.filter(
            ChatMessage.conversation_id == conv.id,
            ChatMessage.sender_id != uid,
            ChatMessage.read_at.is_(None),
        ).count()
        data.append(item)
    return jsonify(data)


@bp.route("/conversations", methods=["POST"])
@jwt_required_compat
def create_conversation():
    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    target = int(data.get("target_user_id") or 0)
    if not target or target == uid:
        return jsonify({"error": "target_user_id ??"}), 400

    if not User.query.get(target):
        return jsonify({"error": "???????"}), 404
    user = User.query.get(uid)
    if not user or user.role != "admin":
        if not users_share_active_class(uid, target):
            return jsonify({"error": "?????????"}), 403
    conv = _get_or_create_conversation(uid, target)
    return jsonify(conv.to_dict(uid))


@bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@jwt_required_compat
def messages(conversation_id):
    uid = get_request_user_id()
    conv = ChatConversation.query.get_or_404(conversation_id)
    if uid not in conv.member_ids():
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "????"}), 403
    rows = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.create_time.asc()).limit(200).all()
    return jsonify([m.to_dict() for m in rows])


@bp.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
@jwt_required_compat
def send_message_rest(conversation_id):
    uid = get_request_user_id()
    conv = ChatConversation.query.get_or_404(conversation_id)
    if uid not in conv.member_ids():
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "????"}), 403
    data = request.get_json(silent=True) or {}
    try:
        msg = _save_message(conv, uid, data.get("content") or "", data.get("msg_type") or "text")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(msg.to_dict()), 201


@bp.route("/conversations/<int:conversation_id>/read", methods=["POST"])
@jwt_required_compat
def mark_read(conversation_id):
    uid = get_request_user_id()
    conv = ChatConversation.query.get_or_404(conversation_id)
    if uid not in conv.member_ids():
        return jsonify({"error": "????"}), 403
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
    if conv.group_id is None:
        other = conv.user2_id if conv.user1_id == sender_id else conv.user1_id
        sender = User.query.get(sender_id)
        if not sender or sender.role != "admin":
            if not users_share_active_class(sender_id, other):
                raise ValueError("?????????")
    content = (content or "").strip()
    if not content:
        raise ValueError("??????")
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
        sub, _, _ = decode_jwt_token(token)
        return sub is not None

    @socketio.on("send_message")
    def socket_send_message(data):  # pragma: no cover
        try:
            sub, err, _ = decode_jwt_token(data.get("token"))
            if err:
                return {"error": err}
            uid = int(sub)
            target = int(data.get("target_user_id") or 0)
            conv_id = data.get("conversation_id")
            conv = ChatConversation.query.get(conv_id) if conv_id else _get_or_create_conversation(uid, target)
            if uid not in conv.member_ids():
                return {"error": "????"}
            if conv.group_id is None:
                other = conv.user2_id if conv.user1_id == uid else conv.user1_id
                user = User.query.get(uid)
                if not user or user.role != "admin":
                    if not users_share_active_class(uid, other):
                        return {"error": "?????????"}
            if False:
                return {"error": "????"}
            msg = _save_message(conv, uid, data.get("content") or "", data.get("msg_type") or "text")
            socketio.emit("message", msg.to_dict(), room=f"user:{conv.user1_id}")
            socketio.emit("message", msg.to_dict(), room=f"user:{conv.user2_id}")
            return msg.to_dict()
        except Exception as exc:
            return {"error": str(exc)}
