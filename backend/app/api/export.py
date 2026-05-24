"""导出 API."""
from flask import Blueprint, Response, request
from app.middleware.auth import admin_required, write_audit
from app.models import GroupInfo, Task, TeamReport, UserProfile
from app.services.export_service import ExportService

bp = Blueprint("export", __name__)
exporter = ExportService()


@bp.route("/<resource_type>", methods=["GET"])
@admin_required
def export_data(resource_type):
    fmt = request.args.get("format", "xlsx")
    group_id = request.args.get("group_id", type=int)

    if resource_type == "profile":
        profiles = UserProfile.query.all()
        data = exporter.export_profiles(profiles)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = "profiles.xlsx"
    elif resource_type == "group":
        groups = GroupInfo.query.all()
        data = exporter.export_groups(groups)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = "groups.xlsx"
    elif resource_type == "task":
        q = Task.query
        if group_id:
            q = q.filter_by(group_id=group_id)
        data = exporter.export_tasks(q.all())
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = "tasks.xlsx"
    elif resource_type == "report":
        if not group_id:
            return {"error": "report 导出需要 group_id"}, 400
        report = TeamReport.query.filter_by(group_id=group_id).order_by(TeamReport.create_time.desc()).first()
        group = GroupInfo.query.get_or_404(group_id)
        if fmt == "pdf" and report:
            data = exporter.export_report_pdf(report, group)
            mime = "application/pdf"
            fname = "report.pdf"
        else:
            return {"error": "无报告或格式不支持"}, 404
    else:
        return {"error": "未知资源类型"}, 400

    write_audit("export", resource_type, group_id, fmt)
    return Response(data, mimetype=mime, headers={"Content-Disposition": f"attachment; filename={fname}"})
