"""NLP 解析引擎测试."""
from app.services.engines.nlp_parser import NLPParser


def test_parse_student_profile():
    parser = NLPParser()
    text = (
        "我是计算机专业本科生，熟悉Python、Java、MySQL、Git、Docker，"
        "擅长软件工程与后端开发，参与过多个团队项目担任技术开发，"
        "沟通表达清晰，风格严谨细致积极主动，偏好技术开发角色。"
    ) * 1
    if len(text) < 50:
        text = text + "补充描述以达到最小长度要求。" * 3
    result = parser.parse(text)
    assert result["identity"] in ("学生", "其他", "职场人士")
    assert result["knowledge_score"] >= 1
    assert result["skill_score"] >= 1
    assert "Python" in result["tech_skills"] or result["skill_score"] > 5


def test_text_too_short():
    parser = NLPParser()
    try:
        parser.parse("太短")
        assert False
    except ValueError:
        pass
