"""团队质量报告 API."""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.middleware.entitlement import paywall_response
from app.models import BehaviorLog, GroupInfo, Task, TeamReport, User
from app.services.ai_insights import team_report_insight
from app.services.entitlement_service import PaywallError, consume_ai_points, get_entitlements

bp = Blueprint("report", __name__)


@bp.route("/<int:group_id>", methods=["GET"])
@jwt_required()
def get_report(group_id):
    uid = get_request_user_id()
    user = User.query.get(uid)
    group = GroupInfo.query.get_or_404(group_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 401
    if user.role != "admin" and uid not in group.member_list():
        return jsonify({"error": "无权访问该报告"}), 403
    report = TeamReport.query.filter_by(group_id=group_id).order_by(TeamReport.create_time.desc()).first()
    if not report:
        return jsonify({"message": "暂无报告"}), 404
    return jsonify(report.to_dict())


@bp.route("/generate", methods=["POST"])
@admin_required
def generate_report():
    data = request.get_json(silent=True) or {}
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id 必填"}), 400

    group = GroupInfo.query.get_or_404(group_id)
    tasks = Task.query.filter_by(group_id=group_id).all()
    logs = BehaviorLog.query.filter_by(group_id=group_id).all()

    completion = sum(t.progress for t in tasks) / max(len(tasks), 1) if tasks else 0
    balance = group.balance_score or 5
    late_count = sum(1 for l in logs if l.submit_status == "late")
    quality = max(0, min(10, completion / 10 + balance / 2 - late_count * 0.5))
    risk = "low"
    if completion < 40 or late_count >= 3:
        risk = "high"
    elif completion < 60:
        risk = "medium"

    detail = {"task_count": len(tasks), "behavior_count": len(logs)}
    use_ai = bool(data.get("use_ai"))
    uid = get_request_user_id()
    if use_ai:
        ent = get_entitlements(uid)
        if not ent["flags"].get("activity_llm_insight"):
            return jsonify({"error": "报告 AI 叙事需升级专业版", "code": "PAYWALL"}), 402
        try:
            consume_ai_points(uid, "report.llm")
        except PaywallError as exc:
            return paywall_response(exc)
        report_stub = {
            "completion_rate": round(completion, 1),
            "balance_score": balance,
            "quality_score": round(quality, 2),
            "risk_level": risk,
        }
        detail["llm_narrative"] = team_report_insight(
            report_stub,
            group.to_dict(),
            [t.to_dict() for t in tasks],
            use_llm=True,
        )

    report = TeamReport(
        group_id=group_id,
        completion_rate=round(completion, 1),
        balance_score=balance,
        quality_score=round(quality, 2),
        risk_level=risk,
        detail=json.dumps(detail, ensure_ascii=False),
    )
    db.session.add(report)
    db.session.commit()
    write_audit("report_generate", "group", group_id)
    out = report.to_dict()
    if detail.get("llm_narrative"):
        out["llm_narrative"] = detail["llm_narrative"]
    return jsonify(out)
