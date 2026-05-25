"""注册所有 API Blueprint."""


def register_blueprints(app):
    from app.api.auth import bp as auth_bp
    from app.api.access import bp as access_bp
    from app.api.health import bp as health_bp
    from app.api.profile import bp as profile_bp
    from app.api.group import bp as group_bp
    from app.api.task import bp as task_bp
    from app.api.board import bp as board_bp
    from app.api.admin import bp as admin_bp
    from app.api.report import bp as report_bp
    from app.api.export import bp as export_bp
    from app.api.behavior import bp as behavior_bp
    from app.api.community import admin_bp as admin_community_bp
    from app.api.community import bp as community_bp
    from app.api.chat import bp as chat_bp
    from app.api.classroom import admin_bp as admin_classroom_bp
    from app.api.classroom import bp as classroom_bp
    from app.api.team_activity import admin_bp as admin_team_activity_bp
    from app.api.team_activity import bp as team_activity_bp
    from app.api.billing import bp as billing_bp
    from app.api.copilot import bp as copilot_bp
    from app.api.rubric import bp as rubric_bp
    from app.api.milestone import bp as milestone_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(group_bp, url_prefix="/api/group")
    app.register_blueprint(task_bp, url_prefix="/api/task")
    app.register_blueprint(behavior_bp, url_prefix="/api/behavior")
    app.register_blueprint(community_bp, url_prefix="/api/community")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(copilot_bp, url_prefix="/api/copilot")
    app.register_blueprint(classroom_bp, url_prefix="/api")
    app.register_blueprint(board_bp, url_prefix="/api/board")
    app.register_blueprint(team_activity_bp, url_prefix="/api/team-activities")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_classroom_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_team_activity_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_community_bp, url_prefix="/api/admin")
    app.register_blueprint(report_bp, url_prefix="/api/report")
    app.register_blueprint(export_bp, url_prefix="/api/export")
    app.register_blueprint(rubric_bp, url_prefix="/api/rubric")
    app.register_blueprint(milestone_bp, url_prefix="/api/milestone")
