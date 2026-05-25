"""班级成员查询辅助."""
from __future__ import annotations

from app.models import ClassMembership, User

ACTIVE_MEMBER = "active"


def active_class_member_ids(class_id: int, *, include_demo: bool = False) -> list[int]:
    rows = ClassMembership.query.filter_by(class_id=class_id, status=ACTIVE_MEMBER).all()
    if not rows:
        return []
    user_ids = [r.user_id for r in rows]
    if include_demo:
        return user_ids
    users = User.query.filter(User.id.in_(user_ids)).all()
    return [u.id for u in users if not u.is_demo]


def filter_user_ids(user_ids: list[int], *, include_demo: bool = False) -> list[int]:
    """过滤用户 ID 列表，默认排除演示账号."""
    if not user_ids:
        return []
    users = User.query.filter(User.id.in_(user_ids)).all()
    if include_demo:
        return [u.id for u in users]
    return [u.id for u in users if not u.is_demo]


def restrict_to_class_members(
    user_ids: list[int],
    class_id: int,
    *,
    include_demo: bool = False,
) -> list[int]:
    """仅保留班级在籍成员（默认排除演示账号）."""
    allowed = set(active_class_member_ids(class_id, include_demo=include_demo))
    return [int(uid) for uid in user_ids if int(uid) in allowed]


def users_share_active_class(uid_a: int, uid_b: int) -> bool:
    if uid_a == uid_b:
        return False
    classes_a = {
        m.class_id
        for m in ClassMembership.query.filter_by(user_id=uid_a, status=ACTIVE_MEMBER).all()
    }
    if not classes_a:
        return False
    return (
        ClassMembership.query.filter(
            ClassMembership.user_id == uid_b,
            ClassMembership.status == ACTIVE_MEMBER,
            ClassMembership.class_id.in_(classes_a),
        ).first()
        is not None
    )
