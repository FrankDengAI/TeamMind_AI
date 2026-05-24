"""NLP 规则解析引擎 - 三维能力画像提取."""
import re
from typing import Any

from app.config import Config
from app.services.engines import keyword_dict as kd


class NLPParser:
    """基于关键词与正则的结构化文本解析器."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        解析文本为三维画像 JSON.
        :param text: 原始文本 50-800 字
        :return: 结构化画像字典
        """
        text = (text or "").strip()
        if len(text) < Config.TEXT_MIN_LEN:
            raise ValueError(f"文本过短，至少需要{Config.TEXT_MIN_LEN}字")
        if len(text) > Config.TEXT_MAX_LEN:
            text = text[: Config.TEXT_MAX_LEN]

        identity = self._match_category(text, kd.IDENTITIES, "其他")
        degree = self._match_category(text, kd.DEGREES, "本科")
        field = self._match_category(text, kd.FIELDS, "交叉学科")
        major = self._match_first(text, kd.MAJORS, "其他")
        theory = self._match_list(text, kd.THEORY_KEYWORDS)
        tech = self._match_list(text, kd.TECH_SKILLS)
        tools = self._match_list(text, kd.TOOL_SKILLS)
        industry = self._match_list(text, kd.INDUSTRY_SKILLS)
        projects = self._extract_projects(text)
        comm = self._parse_comm(text)
        role = self._match_first(text, kd.PREF_ROLES, "执行落地")
        styles = self._match_list(text, kd.COLLAB_STYLES)
        team_exp = self._extract_team_exp(text)

        knowledge_score = self._score_knowledge(degree, major, theory)
        skill_score = self._score_skill(tech, tools, industry, projects)
        collab_score = self._score_collab(comm, role, styles, team_exp)

        return {
            "identity": identity,
            "degree": degree,
            "field": field,
            "major": major,
            "theory_ability": theory,
            "knowledge_score": round(knowledge_score, 1),
            "tech_skills": tech,
            "tool_skills": tools,
            "industry_skills": industry,
            "project_exp": projects,
            "skill_score": round(skill_score, 1),
            "comm_ability": comm,
            "pref_role": role,
            "collab_style": styles,
            "team_exp": team_exp,
            "collab_score": round(collab_score, 1),
        }

    def _match_category(self, text: str, mapping: dict, default: str) -> str:
        for label, kws in mapping.items():
            for kw in kws:
                if kw in text:
                    return label
        return default

    def _match_first(self, text: str, items: list, default: str) -> str:
        for item in items:
            if item in text:
                return item
        return default

    def _match_list(self, text: str, items: list) -> list:
        return [i for i in items if i in text]

    def _parse_comm(self, text: str) -> str:
        if any(k in text for k in kd.COMM_STRONG):
            return "强"
        if any(k in text for k in kd.COMM_WEAK):
            return "弱"
        return "中"

    def _extract_projects(self, text: str) -> list:
        """启发式提取项目经验段落."""
        projects = []
        blocks = re.split(r"(?=[\n\r]|项目[：:])", text)
        for block in blocks:
            if "项目" in block or "负责" in block:
                name_m = re.search(r"项目[名称]*[：:]?\s*([^\s，,。.]{2,20})", block)
                projects.append(
                    {
                        "name": name_m.group(1) if name_m else "未命名项目",
                        "role": self._match_first(block, kd.PREF_ROLES, "成员"),
                        "description": block[:200],
                        "difficulty": 3,
                        "contribution": 0.5,
                    }
                )
        return projects[:5]

    def _extract_team_exp(self, text: str) -> dict:
        exp = {"team_count": 0, "team_scale": "", "duration": ""}
        m = re.search(r"(\d+)\s*[个次项].*团队", text)
        if m:
            exp["team_count"] = int(m.group(1))
        if "合作" in text or "团队" in text:
            exp["team_count"] = max(exp["team_count"], 1)
        return exp

    def _score_knowledge(self, degree: str, major: str, theory: list) -> float:
        degree_map = {"博士": 10, "硕士": 8, "本科": 6, "专家": 10, "高级": 9, "中级": 7, "初级": 5}
        d_score = degree_map.get(degree, 5)
        m_score = 8 if major != "其他" else 4
        t_score = min(10, len(theory) * 1.5 + 3)
        w = Config
        return min(
            10,
            d_score * w.KNOWLEDGE_WEIGHT_DEGREE
            + m_score * w.KNOWLEDGE_WEIGHT_MAJOR
            + t_score * w.KNOWLEDGE_WEIGHT_THEORY,
        )

    def _score_skill(self, tech: list, tools: list, industry: list, projects: list) -> float:
        count = len(tech) + len(tools) + len(industry)
        p_bonus = sum(p.get("difficulty", 3) for p in projects) / max(len(projects), 1)
        w = Config
        base = min(10, count * 0.8 + 2)
        proj = min(10, len(projects) * 1.2 + p_bonus * 0.3)
        return min(10, base * w.SKILL_WEIGHT_COUNT + proj * w.SKILL_WEIGHT_PROJECT + 5 * w.SKILL_WEIGHT_DEPTH)

    def _score_collab(self, comm: str, role: str, styles: list, team_exp: dict) -> float:
        comm_map = {"强": 9, "中": 6, "弱": 3}
        c = comm_map.get(comm, 6)
        r = 8 if role != "执行落地" else 6
        s = min(10, len(styles) * 1.5 + 3)
        t = min(10, team_exp.get("team_count", 0) * 2 + 4)
        w = Config
        return min(
            10,
            c * w.COLLAB_WEIGHT_COMM
            + r * w.COLLAB_WEIGHT_ROLE
            + s * w.COLLAB_WEIGHT_STYLE
            + t * w.COLLAB_WEIGHT_EXP,
        )
