"""导出 API."""
from flask import Blueprint, Response, jsonify, request

from app import db
from app.middleware.auth import admin_required, get_request_user_id, write_audit
from app.middleware.entitlement import paywall_response
from app.models import GroupInfo, Task, TeamReport, UserProfile, UserSubscription
from app.services.entitlement_service import PaywallError, check_limit, consume_ai_points, get_entitlements
from app.services.export_service import ExportService

bp = Blueprint("export", __name__)
exporter = ExportService()


@bp.route("/<resource_type>", methods=["GET"])
@admin_required
def export_data(resource_type):
    fmt = request.args.get("format", "xlsx")
    group_id = request.args.get("group_id", type=int)
    uid = get_request_user_id()
    ent = get_entitlements(uid)
    preview = not ent["flags"]["export_full"]

    try:
        if resource_type == "report" and fmt == "pdf":
            check_limit(uid, "pdf_report")
            consume_ai_points(uid, "export.pdf")
            sub = UserSubscription.query.filter_by(user_id=uid).first()
            if sub:
                sub.pdf_reports_used = (sub.pdf_reports_used or 0) + 1
                db.session.commit()
    except PaywallError as exc:
        return paywall_response(exc)

    if resource_type == "profile":
        profiles = UserProfile.query.all()
        data = exporter.export_profiles(profiles, preview=preview)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = "profiles_preview.xlsx" if preview else "profiles.xlsx"
    elif resource_type == "group":
        groups = GroupInfo.query.all()
        data = exporter.export_groups(groups, preview=preview)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = "groups_preview.xlsx" if preview else "groups.xlsx"
    elif resource_type == "task":
        q = Task.query
        if group_id:
            q = q.filter_by(group_id=group_id)
        data = exporter.export_tasks(q.all(), preview=preview)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = "tasks_preview.xlsx" if preview else "tasks.xlsx"
    elif resource_type == "report":
        if not group_id:
            return jsonify({"error": "report 导出需要 group_id"}), 400
        report = TeamReport.query.filter_by(group_id=group_id).order_by(TeamReport.create_time.desc()).first()
        group = GroupInfo.query.get_or_404(group_id)
        if fmt == "pdf" and report:
            data = exporter.export_report_pdf(report, group, watermark=preview)
            mime = "application/pdf"
            fname = "report.pdf"
        else:
            return jsonify({"error": "无报告或格式不支持"}), 404
    else:
        return jsonify({"error": "未知资源类型"}), 400

    write_audit("export", resource_type, group_id, fmt)
    headers = {"Content-Disposition": f"attachment; filename={fname}"}
    if preview:
        headers["X-TeamMind-Export-Mode"] = "preview"
    return Response(data, mimetype=mime, headers=headers)
