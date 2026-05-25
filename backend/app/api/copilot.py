"""班级 Copilot API."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.middleware.auth import admin_required, get_request_user_id
from app.middleware.entitlement import paywall_response
from app.models import Classroom
from app.services.class_copilot import ask_class_copilot, get_suggested_questions
from app.services.entitlement_service import PaywallError, consume_ai_points, get_entitlements

bp = Blueprint("copilot", __name__)


def _teacher_owns_class(class_id: int, uid: int) -> bool:
    cls = Classroom.query.get(class_id)
    if not cls:
        return False
    return cls.teacher_id == uid or cls.teacher_id is None


@bp.route("/class/<int:class_id>/suggestions", methods=["GET"])
@admin_required
def class_suggestions(class_id):
    uid = get_request_user_id()
    cls = Classroom.query.get_or_404(class_id)
    if cls.teacher_id and cls.teacher_id != uid:
        return jsonify({"error": "无权访问该班级"}), 403
    return jsonify({"questions": get_suggested_questions(class_id)})


@bp.route("/class/<int:class_id>/ask", methods=["POST"])
@admin_required
def class_ask(class_id):
    uid = get_request_user_id()
    cls = Classroom.query.get_or_404(class_id)
    if cls.teacher_id and cls.teacher_id != uid:
        return jsonify({"error": "无权访问该班级"}), 403

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "请输入问题"}), 400
    if len(question) > 500:
        return jsonify({"error": "问题过长（最多 500 字）"}), 400

    ent = get_entitlements(uid)
    if not ent.get("flags", {}).get("class_copilot") and ent.get("plan_code") == "free":
        return jsonify({"error": "班级 Copilot 需升级专业版", "code": "PAYWALL", "feature": "class.copilot"}), 402
    use_llm = bool(ent.get("flags", {}).get("deep_grouping")) or ent.get("plan_code") != "free"
    if use_llm:
        try:
            consume_ai_points(uid, "class.copilot")
        except PaywallError as exc:
            return paywall_response(exc)

    history = data.get("history") or []
    if not isinstance(history, list):
        history = []
    result = ask_class_copilot(class_id, question, use_llm=use_llm, history=history)
    return jsonify({"question": question, "class_id": class_id, **result})
