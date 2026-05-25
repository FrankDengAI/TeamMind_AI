"""Rubric 评分模型 — Phase B."""
from datetime import datetime

from app import db


class Rubric(db.Model):
    __tablename__ = "rubric"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    criteria_json = db.Column(db.Text, default="[]")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def criteria(self) -> list:
        import json

        try:
            data = json.loads(self.criteria_json or "[]")
            return data if isinstance(data, list) else []
        except (TypeError, json.JSONDecodeError):
            return []

    def to_dict(self):
        return {
            "id": self.id,
            "class_id": self.class_id,
            "title": self.title,
            "criteria": self.criteria(),
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class RubricScore(db.Model):
    __tablename__ = "rubric_score"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey("rubric.id"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group_info.id"), nullable=False, index=True)
    scorer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    scores_json = db.Column(db.Text, default="{}")
    comment = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def scores(self) -> dict:
        import json

        try:
            data = json.loads(self.scores_json or "{}")
            return data if isinstance(data, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def to_dict(self):
        return {
            "id": self.id,
            "rubric_id": self.rubric_id,
            "group_id": self.group_id,
            "scorer_id": self.scorer_id,
            "target_user_id": self.target_user_id,
            "scores": self.scores(),
            "comment": self.comment,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
