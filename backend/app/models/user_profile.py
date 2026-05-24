"""用户能力画像模型."""
import json
from datetime import datetime

from app import db


class UserProfile(db.Model):
    """三维能力画像表."""

    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    identity = db.Column(db.String(32))
    degree = db.Column(db.String(32))
    field = db.Column(db.String(32))
    major = db.Column(db.String(64))
    theory_ability = db.Column(db.Text)  # JSON list
    knowledge_score = db.Column(db.Float, default=5.0)
    tech_skills = db.Column(db.Text)
    tool_skills = db.Column(db.Text)
    industry_skills = db.Column(db.Text)
    project_exp = db.Column(db.Text)
    skill_score = db.Column(db.Float, default=5.0)
    comm_ability = db.Column(db.String(16))
    pref_role = db.Column(db.String(64))
    collab_style = db.Column(db.Text)
    team_exp = db.Column(db.Text)
    collab_score = db.Column(db.Float, default=5.0)
    active_tags_json = db.Column(db.Text)
    passive_tags_json = db.Column(db.Text)
    llm_analysis_json = db.Column(db.Text)
    score_breakdown_json = db.Column(db.Text)
    knowledge_final = db.Column(db.Float)
    skill_final = db.Column(db.Float)
    collab_final = db.Column(db.Float)
    raw_source = db.Column(db.String(16))  # text | resume
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def _loads(self, val, default=None):
        if default is None:
            default = []
        if not val:
            return default
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return default

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "identity": self.identity,
            "degree": self.degree,
            "field": self.field,
            "major": self.major,
            "theory_ability": self._loads(self.theory_ability),
            "knowledge_score": self.knowledge_score,
            "tech_skills": self._loads(self.tech_skills),
            "tool_skills": self._loads(self.tool_skills),
            "industry_skills": self._loads(self.industry_skills),
            "project_exp": self._loads(self.project_exp),
            "skill_score": self.skill_score,
            "comm_ability": self.comm_ability,
            "pref_role": self.pref_role,
            "collab_style": self._loads(self.collab_style),
            "team_exp": self._loads(self.team_exp, {}),
            "collab_score": self.collab_score,
            "active_tags": self._loads(self.active_tags_json),
            "passive_tags": self._loads(self.passive_tags_json),
            "llm_analysis": self._loads(self.llm_analysis_json, {}),
            "score_breakdown": self._loads(self.score_breakdown_json, {}),
            "knowledge_final": self.knowledge_final if self.knowledge_final is not None else self.knowledge_score,
            "skill_final": self.skill_final if self.skill_final is not None else self.skill_score,
            "collab_final": self.collab_final if self.collab_final is not None else self.collab_score,
            "raw_source": self.raw_source,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }

    @staticmethod
    def dumps_list(data):
        return json.dumps(data or [], ensure_ascii=False)

    @staticmethod
    def dumps_dict(data):
        return json.dumps(data or {}, ensure_ascii=False)
