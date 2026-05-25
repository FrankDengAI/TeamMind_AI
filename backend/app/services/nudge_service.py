"""班级催办 — 站内通知 MVP."""
from __future__ import annotations

from datetime import datetime

from app import db, socketio
from app.models import ChatConversation, ChatMessage, User
from app.services.classroom_insights import build_nudge_list


def _get_or_create_conversation(uid: int, target: int) -> ChatConversation:
    a, b = sorted([uid, target])
    conv = ChatConversation.query.filter_by(user1_id=a, user2_id=b).first()
    if conv:
        return conv
    conv = ChatConversation(user1_id=a, user2_id=b, last_message_at=datetime.utcnow())
    db.session.add(conv)
    db.session.flush()
    return conv


def send_class_nudges(
    class_id: int,
    teacher_id: int,
    *,
    user_ids: list[int] | None = None,
    custom_message: str | None = None,
) -> dict:
    """向待催办学生发送站内系统消息."""
    payload = build_nudge_list(class_id)
    items = payload.get("items") or []
    if user_ids:
        uid_set = set(int(x) for x in user_ids)
        items = [i for i in items if i.get("user_id") in uid_set]
    if not items:
        return {"sent": 0, "skipped": 0, "items": []}

    teacher = User.query.get(teacher_id)
    teacher_name = teacher.name if teacher else "任课教师"
    default_tpl = f"【{teacher_name}·班级提醒】{{reason}}。请尽快在 TeamMind 完成相关事项。"
    sent = []
    for item in items:
        uid = item.get("user_id")
        if not uid or uid == teacher_id:
            continue
        reason = item.get("reason") or "有待完成事项"
        body = (custom_message or default_tpl).format(reason=reason, name=item.get("name") or "")
        conv = _get_or_create_conversation(teacher_id, uid)
        msg = ChatMessage(
            conversation_id=conv.id,
            sender_id=teacher_id,
            content=body,
            msg_type="system_nudge",
        )
        conv.last_message_at = datetime.utcnow()
        db.session.add(msg)
        db.session.flush()
        sent.append({"user_id": uid, "conversation_id": conv.id, "message_id": msg.id, "reason": reason})
        try:
            socketio.emit(
                "new_message",
                {**msg.to_dict(), "conversation_id": conv.id},
                room=f"user_{uid}",
            )
        except Exception:
            pass

    db.session.commit()
    return {"sent": len(sent), "class_id": class_id, "recipients": sent}
