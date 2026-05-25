"""Rubric API — 教师过程评价."""
import json

from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import admin_required, get_request_user_id, write_audit
from app.middleware.entitlement import paywall_response
from app.models import Classroom, GroupInfo, Rubric, RubricScore
from app.services.entitlement_service import PaywallError, check_limit, get_entitlements

bp = Blueprint("rubric", __name__)


@bp.route("/class/<int:class_id>", methods=["GET", "POST"])
@admin_required
def class_rubrics(class_id):
    Classroom.query.get_or_404(class_id)
    if request.method == "GET":
        rows = Rubric.query.filter_by(class_id=class_id).order_by(Rubric.create_time.desc()).all()
        return jsonify([r.to_dict() for r in rows])
    ent = get_entitlements(get_request_user_id())
    if ent.get("plan_code") == "free":
        return jsonify({"error": "Rubric 需升级专业版", "code": "PAYWALL", "feature": "rubric"}), 402
    try:
        check_limit(get_request_user_id(), "rubric_sets", current=Rubric.query.filter_by(class_id=class_id).count())
    except PaywallError as exc:
        return paywall_response(exc)
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip() or "过程评价量表"
    criteria = data.get("criteria") or [
        {"key": "contribution", "label": "贡献度", "max": 5},
        {"key": "collaboration", "label": "协作", "max": 5},
        {"key": "quality", "label": "交付质量", "max": 5},
    ]
    row = Rubric(class_id=class_id, title=title, criteria_json=json.dumps(criteria, ensure_ascii=False))
    db.session.add(row)
    db.session.commit()
    write_audit("rubric_create", "rubric", row.id)
    return jsonify(row.to_dict()), 201


@bp.route("/<int:rubric_id>/scores", methods=["GET", "POST"])
@admin_required
def rubric_scores(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    if request.method == "GET":
        group_id = request.args.get("group_id", type=int)
        q = RubricScore.query.filter_by(rubric_id=rubric_id)
        if group_id:
            q = q.filter_by(group_id=group_id)
        return jsonify([s.to_dict() for s in q.all()])
    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    target_user_id = data.get("target_user_id")
    if not group_id or not target_user_id:
        return jsonify({"error": "group_id 与 target_user_id 必填"}), 400
    GroupInfo.query.get_or_404(group_id)
    scorer_id = get_request_user_id()
    existing = RubricScore.query.filter_by(
        rubric_id=rubric_id, group_id=group_id, target_user_id=target_user_id, scorer_id=scorer_id
    ).first()
    scores = data.get("scores") or {}
    comment = (data.get("comment") or "").strip()
    if existing:
        existing.scores_json = json.dumps(scores, ensure_ascii=False)
        existing.comment = comment
        db.session.commit()
        return jsonify(existing.to_dict())
    row = RubricScore(
        rubric_id=rubric_id,
        group_id=group_id,
        scorer_id=scorer_id,
        target_user_id=target_user_id,
        scores_json=json.dumps(scores, ensure_ascii=False),
        comment=comment,
    )
    db.session.add(row)
    db.session.commit()
    write_audit("rubric_score", "rubric", rubric_id)
    return jsonify(row.to_dict()), 201
