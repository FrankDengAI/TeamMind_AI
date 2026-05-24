"""班级、成员与审批申请模型."""
from __future__ import annotations

import json
from datetime import datetime

from app import db


class Classroom(db.Model):
    """大学课程班级."""

    __tablename__ = "classroom"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    code = db.Column(db.String(64), unique=True, index=True)
    major = db.Column(db.String(120))
    grade = db.Column(db.String(32))
    course_name = db.Column(db.String(120))
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    max_students = db.Column(db.Integer, default=20)
    status = db.Column(db.String(32), default="active", index=True)
    description = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, *, member_count: int | None = None, pending_count: int | None = None, teacher=None, advice: dict | None = None):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "major": self.major,
            "grade": self.grade,
            "course_name": self.course_name,
            "teacher_id": self.teacher_id,
            "teacher": teacher.to_dict() if hasattr(teacher, "to_dict") else teacher,
            "max_students": self.max_students,
            "status": self.status,
            "description": self.description,
            "member_count": member_count,
            "pending_count": pending_count,
            "grouping_advice": advice,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }


class ClassMembership(db.Model):
    """学生在某班级中的当前状态."""

    __tablename__ = "class_membership"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    status = db.Column(db.String(32), default="pending_join", index=True)
    source = db.Column(db.String(32), default="student_request")
    joined_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)
    request_id = db.Column(db.Integer, db.ForeignKey("class_request.id"))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, user=None, classroom=None):
        return {
            "id": self.id,
            "class_id": self.class_id,
            "user_id": self.user_id,
            "status": self.status,
            "source": self.source,
            "user": user.to_dict() if hasattr(user, "to_dict") else user,
            "classroom": classroom.to_dict() if hasattr(classroom, "to_dict") else classroom,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
            "request_id": self.request_id,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }


class ClassRequest(db.Model):
    """学生加入或退出班级的审批记录."""

    __tablename__ = "class_request"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    request_type = db.Column(db.String(32), nullable=False, index=True)  # join | leave
    status = db.Column(db.String(32), default="pending", index=True)
    message = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    reviewed_note = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    snapshot_json = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def snapshot(self):
        if not self.snapshot_json:
            return {}
        try:
            return json.loads(self.snapshot_json)
        except (TypeError, json.JSONDecodeError):
            return {}

    def to_dict(self, user=None, classroom=None, reviewer=None):
        return {
            "id": self.id,
            "class_id": self.class_id,
            "user_id": self.user_id,
            "request_type": self.request_type,
            "status": self.status,
            "message": self.message,
            "reviewed_by": self.reviewed_by,
            "reviewed_note": self.reviewed_note,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "snapshot": self.snapshot(),
            "user": user.to_dict() if hasattr(user, "to_dict") else user,
            "classroom": classroom.to_dict() if hasattr(classroom, "to_dict") else classroom,
            "reviewer": reviewer.to_dict() if hasattr(reviewer, "to_dict") else reviewer,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }
