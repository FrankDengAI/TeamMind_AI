"""多教师数据隔离：班级归属校验."""
from __future__ import annotations

from app.models import Classroom, User


def bootstrap_admin_id() -> int | None:
    admin = User.query.filter_by(role="admin").order_by(User.id.asc()).first()
    return admin.id if admin else None


def admin_owns_class(cls: Classroom | None, admin_id: int) -> bool:
    if not cls:
        return False
    if cls.teacher_id is None:
        return admin_id == bootstrap_admin_id()
    return int(cls.teacher_id) == int(admin_id)


def teacher_classroom_query(admin_id: int):
    bid = bootstrap_admin_id()
    if admin_id == bid:
        return Classroom.query.filter(
            (Classroom.teacher_id == admin_id) | (Classroom.teacher_id.is_(None))
        )
    return Classroom.query.filter_by(teacher_id=admin_id)
