"""组队活动与自由组队模型."""
import json
from datetime import datetime

from app import db


class TeamActivity(db.Model):
    """老师发起的一次组队活动."""

    __tablename__ = "team_activity"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    course_name = db.Column(db.String(120))
    mode = db.Column(db.String(32), default="task_auto", index=True)  # task_auto | free_team
    status = db.Column(db.String(32), default="draft", index=True)
    group_size = db.Column(db.Integer, default=4)
    task_goal = db.Column(db.Text)
    required_tags_json = db.Column(db.Text)
    required_roles_json = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), index=True, nullable=False)
    ai_insight_json = db.Column(db.Text)  # 活动级 AI 复盘缓存
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def required_tags(self):
        return _loads(self.required_tags_json, [])

    def required_roles(self):
        return _loads(self.required_roles_json, [])

    def to_dict(self, *, counts: dict | None = None):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "course_name": self.course_name,
            "mode": self.mode,
            "status": self.status,
            "group_size": self.group_size,
            "task_goal": self.task_goal,
            "required_tags": self.required_tags(),
            "required_roles": self.required_roles(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "class_id": self.class_id,
            "created_by": self.created_by,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }
        if counts:
            data.update(counts)
        return data


class TeamActivityParticipant(db.Model):
    """学员参与某次组队活动的记录."""

    __tablename__ = "team_activity_participant"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("team_activity.id"), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    status = db.Column(db.String(32), default="joined", index=True)
    active_tags_json = db.Column(db.Text)
    passive_tags_json = db.Column(db.Text)
    profile_snapshot_json = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "status": self.status,
            "active_tags": _loads(self.active_tags_json, []),
            "passive_tags": _loads(self.passive_tags_json, []),
            "profile_snapshot": _loads(self.profile_snapshot_json, {}),
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class TeamRoom(db.Model):
    """自由组队模式下的学生队伍."""

    __tablename__ = "team_room"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("team_activity.id"), index=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    leader_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    member_ids_json = db.Column(db.Text)
    desired_tags_json = db.Column(db.Text)
    status = db.Column(db.String(32), default="open", index=True)  # open | locked | closed
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), index=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def member_ids(self):
        return _loads(self.member_ids_json, [])

    def set_member_ids(self, ids):
        self.member_ids_json = json.dumps(list(dict.fromkeys([int(x) for x in ids])), ensure_ascii=False)

    def to_dict(self, users_by_id: dict | None = None):
        mids = self.member_ids()
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "name": self.name,
            "description": self.description,
            "leader_id": self.leader_id,
            "member_ids": mids,
            "members": [users_by_id.get(mid) for mid in mids if users_by_id and users_by_id.get(mid)],
            "desired_tags": _loads(self.desired_tags_json, []),
            "status": self.status,
            "group_id": self.group_id,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class TeamJoinRequest(db.Model):
    """自由组队加入申请."""

    __tablename__ = "team_join_request"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("team_activity.id"), index=True, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team_room.id"), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(32), default="pending", index=True)  # pending | approved | rejected
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, user=None):
        user_data = user.to_dict() if hasattr(user, "to_dict") else user
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "user": user_data if user_data else None,
            "message": self.message,
            "status": self.status,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class TeamConfirmation(db.Model):
    """候选分组预沟通确认与微调申请."""

    __tablename__ = "team_confirmation"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("team_activity.id"), index=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    status = db.Column(db.String(32), default="pending", index=True)  # pending|accepted|adjust_requested|resolved|rejected
    accept_team = db.Column(db.Boolean, default=False)
    accept_role = db.Column(db.Boolean, default=False)
    preferred_role = db.Column(db.String(64))
    task_preferences_json = db.Column(db.Text)
    reason = db.Column(db.Text)
    message = db.Column(db.Text)
    handled_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    handled_note = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def task_preferences(self):
        return _loads(self.task_preferences_json, [])

    def to_dict(self, user=None):
        user_data = user.to_dict() if hasattr(user, "to_dict") else user
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "user": user_data if user_data else None,
            "status": self.status,
            "accept_team": bool(self.accept_team),
            "accept_role": bool(self.accept_role),
            "preferred_role": self.preferred_role,
            "task_preferences": self.task_preferences(),
            "reason": self.reason,
            "message": self.message,
            "handled_by": self.handled_by,
            "handled_note": self.handled_note,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }


def _loads(raw, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default
