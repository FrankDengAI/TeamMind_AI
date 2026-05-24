"""画像采集与解析 API."""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.config import Config
from app.middleware.auth import get_request_user_id, write_audit
from app.models import UserProfile
from app.services.engines.deepseek_parser import DeepSeekParser
from app.services.engines.nlp_parser import NLPParser
from app.services.engines.resume_parser import ResumeParser
from app.services.passive_tag_pipeline import PassiveTagPipeline
from app.services.profile_scoring import ProfileScoringEngine
from app.services.tag_catalog import load_tag_catalog, normalize_active_tags

bp = Blueprint("profile", __name__)
nlp = NLPParser()
resume_engine = ResumeParser()
deepseek = DeepSeekParser()
scoring = ProfileScoringEngine()
passive_pipeline = PassiveTagPipeline()

_DIM_LABELS = {
    "knowledge": "知识",
    "skill": "技能",
    "collab": "协作",
    "custom": "自定义",
}


def _parse_json_field(value, default=None):
    if default is None:
        default = []
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON 字段格式错误") from exc


def _ensure_profile_text(raw: str, active_tags) -> str:
    """自由描述可选；至少选择主动标签，或输入足够长度的自由描述."""
    text = (raw or "").strip()
    normalized = normalize_active_tags(active_tags)
    if not normalized and len(text) < Config.TEXT_MIN_LEN:
        raise ValueError(f"请至少选择主动标签，或输入{Config.TEXT_MIN_LEN}字以上自由描述")

    if len(text) >= Config.TEXT_MIN_LEN:
        return text[: Config.TEXT_MAX_LEN]

    by_dim: dict[str, list[str]] = {}
    for tag in normalized:
        dim = str(tag.get("dimension") or "custom")
        name = str(tag.get("name") or "").strip()
        if name:
            by_dim.setdefault(dim, []).append(name)

    segments = []
    for dim in ("knowledge", "skill", "collab", "custom"):
        names = by_dim.get(dim) or []
        if names:
            label = _DIM_LABELS.get(dim, dim)
            segments.append(f"{label}（{'、'.join(names)}）")

    tag_sentence = "主动标签：" + "；".join(segments) if segments else ""
    if text and tag_sentence:
        text = f"{text} {tag_sentence}"
    elif tag_sentence:
        text = (
            f"{tag_sentence}。"
            "以上标签用于整理项目角色建议，希望参与团队项目并完成与自身能力和偏好匹配的任务分工。"
        )

    filler = "请基于主动标签整理学习方向、技能特点与协作方式，用于后续分组参考。"
    while len(text) < Config.TEXT_MIN_LEN:
        text = f"{text} {filler}".strip()

    return text[: Config.TEXT_MAX_LEN]


def _save_profile(user_id: int, parsed: dict, source: str) -> UserProfile:
    prof = UserProfile(
        user_id=user_id,
        identity=parsed.get("identity"),
        degree=parsed.get("degree"),
        field=parsed.get("field"),
        major=parsed.get("major"),
        theory_ability=UserProfile.dumps_list(parsed.get("theory_ability")),
        knowledge_score=parsed.get("knowledge_score", 5),
        tech_skills=UserProfile.dumps_list(parsed.get("tech_skills")),
        tool_skills=UserProfile.dumps_list(parsed.get("tool_skills")),
        industry_skills=UserProfile.dumps_list(parsed.get("industry_skills")),
        project_exp=UserProfile.dumps_list(parsed.get("project_exp")),
        skill_score=parsed.get("skill_score", 5),
        comm_ability=parsed.get("comm_ability"),
        pref_role=parsed.get("pref_role"),
        collab_style=UserProfile.dumps_list(parsed.get("collab_style")),
        team_exp=UserProfile.dumps_dict(parsed.get("team_exp")),
        collab_score=parsed.get("collab_score", 5),
        raw_source=source,
    )
    db.session.add(prof)
    db.session.commit()
    return prof


def _save_composite_profile(user_id: int, parsed: dict, payload: dict, source: str) -> UserProfile:
    prof = UserProfile(
        user_id=user_id,
        identity=parsed.get("identity"),
        degree=payload.get("degree") or parsed.get("degree"),
        field=parsed.get("field"),
        major=payload.get("major") or parsed.get("major"),
        theory_ability=UserProfile.dumps_list(parsed.get("theory_ability")),
        knowledge_score=payload.get("knowledge_score", parsed.get("knowledge_score", 5)),
        tech_skills=UserProfile.dumps_list(parsed.get("tech_skills")),
        tool_skills=UserProfile.dumps_list(parsed.get("tool_skills")),
        industry_skills=UserProfile.dumps_list(parsed.get("industry_skills")),
        project_exp=UserProfile.dumps_list(parsed.get("project_exp")),
        skill_score=payload.get("skill_score", parsed.get("skill_score", 5)),
        comm_ability=parsed.get("comm_ability"),
        pref_role=payload.get("pref_role") or parsed.get("pref_role"),
        collab_style=UserProfile.dumps_list(parsed.get("collab_style")),
        team_exp=UserProfile.dumps_dict(parsed.get("team_exp")),
        collab_score=payload.get("collab_score", parsed.get("collab_score", 5)),
        active_tags_json=json.dumps(payload.get("active_tags") or [], ensure_ascii=False),
        passive_tags_json=json.dumps(payload.get("passive_tags") or [], ensure_ascii=False),
        llm_analysis_json=json.dumps(payload.get("llm_analysis") or {}, ensure_ascii=False),
        score_breakdown_json=json.dumps(payload.get("score_breakdown") or {}, ensure_ascii=False),
        knowledge_final=payload.get("knowledge_final"),
        skill_final=payload.get("skill_final"),
        collab_final=payload.get("collab_final"),
        raw_source=source,
    )
    db.session.add(prof)
    db.session.commit()
    return prof


def _build_composite(user_id: int, raw: str, active_tags, source: str):
    parsed = nlp.parse(raw)
    normalized_tags = normalize_active_tags(active_tags)
    llm_analysis = {}
    llm_error = None
    try:
        if raw.strip() or normalized_tags:
            llm_analysis = deepseek.parse_profile(raw, normalized_tags)
    except Exception as e:  # noqa: BLE001
        llm_error = str(e)
    payload = scoring.build_profile_payload(
        active_tags=normalized_tags,
        llm_analysis=llm_analysis,
        rule_result=parsed,
        passive_tags=[],
        user_id=user_id,
    )
    prof = _save_composite_profile(user_id, parsed, payload, source)
    write_audit("profile_submit", "profile", prof.id, json.dumps({"source": source, "llm_error": llm_error}, ensure_ascii=False))
    data = {"profile": prof.to_dict(), "parsed": parsed, "llm_analysis": llm_analysis, "score_breakdown": payload["score_breakdown"]}
    if llm_error:
        data["llm_error"] = llm_error
    return data


@bp.route("/tags/catalog", methods=["GET"])
@jwt_required()
def tag_catalog():
    return jsonify(load_tag_catalog())


@bp.route("/current", methods=["GET"])
@jwt_required()
def current_profile():
    uid = get_request_user_id()
    prof = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()
    return jsonify(prof.to_dict() if prof else {})


@bp.route("/submit", methods=["POST"])
@jwt_required()
def submit_profile():
    uid = get_request_user_id()
    try:
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            raw = (request.form.get("free_text") or request.form.get("raw_text") or "").strip()
            active_tags = _parse_json_field(request.form.get("active_tags") or "[]")
            if "resume_file" in request.files and request.files["resume_file"].filename:
                f = request.files["resume_file"]
                content = f.read()
                ext = resume_engine.validate_file(f.filename, content)
                path = resume_engine.save_upload(uid, f.filename, content)
                raw = (raw + "\n" + resume_engine.extract_text(path, ext)).strip()
                source = "resume"
            else:
                source = "text"
        else:
            data = request.get_json(silent=True) or {}
            raw = (data.get("free_text") or data.get("raw_text") or "").strip()
            active_tags = data.get("active_tags") or []
            source = "text"
        raw = _ensure_profile_text(raw, active_tags)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if len(raw) > Config.TEXT_MAX_LEN:
        raw = raw[: Config.TEXT_MAX_LEN]
    try:
        return jsonify(_build_composite(uid, raw, active_tags, source))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "画像生成失败", "detail": str(e)}), 422


@bp.route("/recalculate", methods=["POST"])
@jwt_required()
def recalculate_profile():
    uid = get_request_user_id()
    prof = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).first()
    if not prof:
        return jsonify({"error": "暂无画像"}), 404
    passive_pipeline.recalculate_profile(prof)
    return jsonify(prof.to_dict())


@bp.route("/parse", methods=["POST"])
@jwt_required()
def parse_text():
    uid = get_request_user_id()
    data = request.get_json(silent=True) or {}
    raw = (data.get("raw_text") or "").strip()
    active_tags = data.get("active_tags") or []
    try:
        raw = _ensure_profile_text(raw, active_tags)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        return jsonify(_build_composite(uid, raw, active_tags, "text"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "解析失败", "detail": str(e)}), 422


@bp.route("/resume", methods=["POST"])
@jwt_required()
def parse_resume():
    uid = get_request_user_id()
    if "resume_file" not in request.files:
        return jsonify({"error": "请上传 resume_file"}), 400
    f = request.files["resume_file"]
    if not f.filename:
        return jsonify({"error": "文件名为空"}), 400
    content = f.read()
    try:
        ext = resume_engine.validate_file(f.filename, content)
        path = resume_engine.save_upload(uid, f.filename, content)
        text = resume_engine.extract_text(path, ext)
        if len(text) < Config.TEXT_MIN_LEN:
            text = text + " " * (Config.TEXT_MIN_LEN - len(text) + 1)  # 补齐供解析
        raw = text[: Config.TEXT_MAX_LEN]
        active_tags = _parse_json_field(request.form.get("active_tags") or "[]") if request.form else []
        return jsonify(_build_composite(uid, raw, active_tags, "resume"))
    except ValueError as e:
        msg = str(e)
        if "不支持" in msg or "格式" in msg:
            return jsonify({"error": msg}), 415
        return jsonify({"error": msg}), 422
    except Exception as e:
        return jsonify({"error": "简历解析失败", "detail": str(e)}), 422


@bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    uid = get_request_user_id()
    profiles = UserProfile.query.filter_by(user_id=uid).order_by(UserProfile.create_time.desc()).all()
    return jsonify([p.to_dict() for p in profiles])


@bp.route("/<int:profile_id>", methods=["GET"])
@jwt_required()
def get_profile(profile_id):
    uid = get_request_user_id()
    prof = UserProfile.query.get_or_404(profile_id)
    if prof.user_id != uid:
        from app.models import User

        u = User.query.get(uid)
        if not u or u.role != "admin":
            return jsonify({"error": "无权访问"}), 403
    return jsonify(prof.to_dict())


@bp.route("/<int:profile_id>", methods=["PUT"])
@jwt_required()
def update_profile(profile_id):
    uid = get_request_user_id()
    prof = UserProfile.query.get_or_404(profile_id)
    if prof.user_id != uid:
        return jsonify({"error": "无权修改"}), 403
    data = request.get_json(silent=True) or {}
    for key in (
        "identity", "degree", "field", "major", "comm_ability", "pref_role",
        "knowledge_score", "skill_score", "collab_score", "knowledge_final", "skill_final", "collab_final",
    ):
        if key in data:
            setattr(prof, key, data[key])
    for key, col in [
        ("theory_ability", "theory_ability"),
        ("tech_skills", "tech_skills"),
        ("tool_skills", "tool_skills"),
        ("industry_skills", "industry_skills"),
        ("project_exp", "project_exp"),
        ("collab_style", "collab_style"),
        ("team_exp", "team_exp"),
        ("active_tags", "active_tags_json"),
        ("passive_tags", "passive_tags_json"),
        ("llm_analysis", "llm_analysis_json"),
        ("score_breakdown", "score_breakdown_json"),
    ]:
        if key in data:
            val = data[key]
            setattr(prof, col, json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else val)
    db.session.commit()
    write_audit("profile_update", "profile", prof.id)
    return jsonify(prof.to_dict())
