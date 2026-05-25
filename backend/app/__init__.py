"""TeamMind AI Flask 应用工厂."""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()
try:
    from flask_socketio import SocketIO

    socketio = SocketIO(async_mode="threading")
except Exception:  # pragma: no cover - optional realtime dependency
    socketio = None


def create_app(config_class=Config, serve_static=False, static_ui=None):
    """创建并配置 Flask 应用."""
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    _validate_runtime_config(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}}, supports_credentials=True)

    db.init_app(app)
    jwt.init_app(app)
    if socketio is not None:
        socketio.init_app(app, cors_allowed_origins=app.config.get("SOCKETIO_CORS_ORIGINS", "*"))

    from app.api import register_blueprints

    register_blueprints(app)

    if serve_static:
        from flask import abort, send_from_directory

        from app.static_paths import frontend_source_name, resolve_admin_dir, resolve_frontend_dir, resolve_portal_dir

        if static_ui == "portal":
            static_root = resolve_portal_dir()
        elif static_ui == "admin":
            static_root = resolve_admin_dir()
        elif static_ui == "user":
            static_root = resolve_frontend_dir()
        else:
            static_root = resolve_frontend_dir()
        app.config["FRONTEND_STATIC_ROOT"] = str(static_root)

        def _serve_static_root(root, path):
            if path:
                target = (root / path).resolve()
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    abort(404)
                if target.is_file():
                    return send_from_directory(root, path)
            index = root / "index.html"
            if index.is_file():
                return send_from_directory(root, "index.html")
            return jsonify({"error": "前端资源缺失", "static_root": str(root)}), 404

        if static_ui == "portal":
            admin_root = resolve_admin_dir()
            student_root = resolve_frontend_dir()

            @app.route("/admin/assets/<path:filename>")
            def serve_admin_assets(filename):
                return send_from_directory(admin_root / "assets", filename)

            @app.route("/student/assets/<path:filename>")
            def serve_student_assets(filename):
                return send_from_directory(student_root / "assets", filename)

            @app.route("/admin/", defaults={"path": ""})
            @app.route("/admin/<path:path>")
            def serve_admin_spa(path):
                return _serve_static_root(admin_root, path)

            @app.route("/student/", defaults={"path": ""})
            @app.route("/student/<path:path>")
            def serve_student_spa(path):
                return _serve_static_root(student_root, path)

        @app.route("/assets/<path:filename>")
        def serve_assets(filename):
            return send_from_directory(static_root / "assets", filename)

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_spa(path):
            # API 由 Blueprint 处理；此处仅兜底非 API 的浏览器路由
            if path.startswith("api/") or path == "api":
                abort(404)
            return _serve_static_root(static_root, path)

        print(f"[TeamMind] 已托管前端: {frontend_source_name(static_ui)} -> {static_root}")

    from flask import send_from_directory

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    @app.errorhandler(400)
    def bad_request(e):
        return _error_response("参数错误", e, 400)

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "文件过大", "max_mb": 10}), 413

    @app.errorhandler(415)
    def unsupported(e):
        return jsonify({"error": "不支持的文件格式"}), 415

    @app.errorhandler(422)
    def unprocessable(e):
        return _error_response("解析失败", e, 422)

    @app.errorhandler(500)
    def internal(e):
        return _error_response("服务异常", e, 500)

    @jwt.unauthorized_loader
    def missing_token(cb):
        return jsonify({"error": "未登录或令牌无效"}), 401

    @jwt.invalid_token_loader
    def invalid_token(cb):
        return jsonify({"error": "未登录或令牌无效"}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "登录已过期，请重新登录"}), 401

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return jsonify({"error": "登录已失效，请重新登录"}), 401

    with app.app_context():
        db.create_all()
        _ensure_runtime_schema()
        _seed_billing_plans()
        if not app.config.get("TESTING"):
            _seed_demo_classes()
            _seed_demo_content()
            _seed_demo_activities()
            _seed_demo_enrichment()

    try:
        from app.scheduler.jobs import start_scheduler

        start_scheduler(app)
    except Exception:
        pass

    return app


def _error_response(message, exc, status):
    from flask import current_app

    payload = {"error": message}
    if current_app.config.get("DEBUG") or current_app.config.get("TESTING") or not current_app.config.get("IS_PRODUCTION"):
        payload["detail"] = str(exc)
    return jsonify(payload), status


def _validate_runtime_config(app):
    """公网/生产模式下拒绝使用开发默认安全配置."""
    if not app.config.get("IS_PRODUCTION"):
        return
    weak_values = {
        "SECRET_KEY": "teammind-dev-secret-change-in-prod",
        "JWT_SECRET_KEY": "teamforge-jwt-secret",
    }
    for key, default in weak_values.items():
        if app.config.get(key) == default:
            raise RuntimeError(f"生产环境必须通过环境变量设置 {key}")
    if app.config.get("CORS_ORIGINS") == "*":
        raise RuntimeError("生产环境必须通过 TEAMMIND_CORS_ORIGINS 设置明确的前端域名白名单")


def _ensure_runtime_schema():
    """为已有 SQLite 数据库补齐新版本列；新表由 db.create_all 创建."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "user_profile" not in table_names:
        return
    cols = {c["name"] for c in inspector.get_columns("user_profile")}
    additions = {
        "active_tags_json": "TEXT",
        "passive_tags_json": "TEXT",
        "llm_analysis_json": "TEXT",
        "score_breakdown_json": "TEXT",
        "knowledge_final": "REAL",
        "skill_final": "REAL",
        "collab_final": "REAL",
    }
    for name, col_type in additions.items():
        if name not in cols:
            db.session.execute(text(f"ALTER TABLE user_profile ADD COLUMN {name} {col_type}"))
    if "user" in table_names:
        user_cols = {c["name"] for c in inspector.get_columns("user")}
        user_additions = {
            "avatar_url": "VARCHAR(512)",
            "bio": "VARCHAR(240)",
            "headline": "VARCHAR(120)",
            "portfolio_url": "VARCHAR(512)",
            "github_url": "VARCHAR(512)",
            "research_interest": "VARCHAR(240)",
            "availability": "VARCHAR(120)",
            "display_theme": "VARCHAR(32)",
        }
        for name, col_type in user_additions.items():
            if name not in user_cols:
                db.session.execute(text(f"ALTER TABLE user ADD COLUMN {name} {col_type}"))
    if "group_info" in table_names:
        group_cols = {c["name"] for c in inspector.get_columns("group_info")}
        if "activity_id" not in group_cols:
            db.session.execute(text("ALTER TABLE group_info ADD COLUMN activity_id INTEGER"))
    if "team_activity" in table_names:
        activity_cols = {c["name"] for c in inspector.get_columns("team_activity")}
        if "class_id" not in activity_cols:
            db.session.execute(text("ALTER TABLE team_activity ADD COLUMN class_id INTEGER"))
        if "ai_insight_json" not in activity_cols:
            db.session.execute(text("ALTER TABLE team_activity ADD COLUMN ai_insight_json TEXT"))
    if "classroom" in table_names:
        class_cols = {c["name"] for c in inspector.get_columns("classroom")}
        if "timeline_json" not in class_cols:
            db.session.execute(text("ALTER TABLE classroom ADD COLUMN timeline_json TEXT"))
    if "chat_conversation" in table_names:
        chat_cols = {c["name"] for c in inspector.get_columns("chat_conversation")}
        if "group_id" not in chat_cols:
            db.session.execute(text("ALTER TABLE chat_conversation ADD COLUMN group_id INTEGER"))
    if "behavior_log" in table_names:
        behavior_cols = {c["name"] for c in inspector.get_columns("behavior_log")}
        behavior_additions = {
            "event_type": "VARCHAR(32) DEFAULT 'progress'",
            "detail": "TEXT",
        }
        for name, col_type in behavior_additions.items():
            if name not in behavior_cols:
                db.session.execute(text(f"ALTER TABLE behavior_log ADD COLUMN {name} {col_type}"))
    db.session.commit()


def _seed_billing_plans():
    """同步套餐表并确保演示管理员有免费订阅记录."""
    import json

    from app.models import SubscriptionPlan, User, UserSubscription
    from app.services.plan_catalog import PLAN_CATALOG

    for code, plan in PLAN_CATALOG.items():
        row = SubscriptionPlan.query.filter_by(code=code).first()
        meta = {
            "name_en": plan.get("name_en"),
            "badge": plan.get("badge"),
            "highlight": plan.get("highlight"),
            "features": plan.get("features_marketing", []),
        }
        if not row:
            row = SubscriptionPlan(
                code=code,
                name=plan["name"],
                limits_json=json.dumps(plan["limits"], ensure_ascii=False),
                price_month_cents=plan["price_month_cents"],
                price_year_cents=plan["price_year_cents"],
                meta_json=json.dumps(meta, ensure_ascii=False),
            )
            db.session.add(row)
        else:
            row.name = plan["name"]
            row.limits_json = json.dumps(plan["limits"], ensure_ascii=False)
            row.price_month_cents = plan["price_month_cents"]
            row.price_year_cents = plan["price_year_cents"]
            row.meta_json = json.dumps(meta, ensure_ascii=False)
    admin = User.query.filter_by(account="admin").first()
    if admin and not UserSubscription.query.filter_by(user_id=admin.id).first():
        db.session.add(UserSubscription(user_id=admin.id, plan_code="free", status="active"))
    db.session.commit()


def _seed_demo_content():
    """补齐贴近课堂项目的社区内容，作者均来自数据库中的学生用户."""
    import json
    from pathlib import Path

    import bcrypt

    from app.models import CommunityPost, PostComment, PostInteraction, User

    def _tag_list(raw_tags):
        return [{"name": name, "dimension": dimension} for name, dimension in raw_tags]

    def _media_json(url, name):
        if not url:
            return "[]"
        return json.dumps([{"type": "image", "url": url, "name": name}], ensure_ascii=False)

    root = Path(__file__).resolve().parents[2]
    seed_path = root / "database" / "seeds" / "demo_posts.json"
    if seed_path.is_file():
        demo_posts = json.loads(seed_path.read_text(encoding="utf-8"))
    else:
        demo_posts = [
            {
                "account": "zhangsan",
                "title": "想找一起做数据可视化项目的队友",
                "content": "我最近在学习 Python、Pandas 和可视化，希望找一两个同学一起做课程项目。我可以负责数据清洗和图表实现，也想学习大家的展示思路。",
                "tags": [["Python", "skill"], ["数据分析", "skill"], ["主动沟通", "collab"]],
                "media": "",
            },
            {
                "account": "wangwu",
                "title": "前端原型和交互设计资源分享",
                "content": "整理了一些 Figma 原型、Element Plus 页面结构和用户流程设计资料，适合做产品原型或后台管理页面的同学参考。也欢迎一起讨论界面怎么更清晰。",
                "tags": [["前端开发", "skill"], ["UI设计", "skill"], ["乐于分享", "collab"]],
                "media": "",
            },
            {
                "account": "qianqi",
                "title": "项目汇报分工经验",
                "content": "上次小组项目里，我们把汇报拆成背景、方案、演示、复盘四块，每个人都有明确部分。提前排练一次能明显减少临场混乱，文档同学也能更好地串联内容。",
                "tags": [["文档汇报", "collab"], ["协调对接", "collab"], ["严谨细致", "collab"]],
                "media": "",
            },
        ]

    students = User.query.filter_by(role="user").order_by(User.id.asc()).all()
    if not students:
        password_hash = bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode()
        for idx, item in enumerate(demo_posts[:6], start=1):
            user = User(
                name=f"演示同学{idx:02d}",
                account=item.get("account") or f"demo_student_{idx:02d}",
                password_hash=password_hash,
                role="user",
                bio="用于初始化学习社区示例内容",
            )
            db.session.add(user)
            students.append(user)
        db.session.flush()

    users_by_account = {user.account: user for user in students}
    existing_titles = {title for (title,) in db.session.query(CommunityPost.title).all()}

    legacy_title_authors = {
        "想找一起做数据可视化项目的队友": "zhangsan",
        "前端原型和交互设计资源分享": "wangwu",
        "项目汇报分工经验": "qianqi",
    }
    legacy_author_accounts = {"zhangsan", "demo_student"}
    users_by_id = {user.id: user for user in students}
    for title, account in legacy_title_authors.items():
        post = CommunityPost.query.filter_by(title=title).first()
        target_user = users_by_account.get(account)
        current_user = users_by_id.get(post.user_id) if post else None
        if post and target_user and current_user and current_user.account in legacy_author_accounts:
            post.user_id = target_user.id

    managed_titles = set(legacy_title_authors)
    for idx, item in enumerate(demo_posts):
        managed_titles.add(item["title"])
        if item["title"] in existing_titles:
            continue
        author = users_by_account.get(item.get("account")) or students[idx % len(students)]
        db.session.add(
            CommunityPost(
                user_id=author.id,
                title=item["title"],
                content=item["content"],
                media_json=_media_json(item.get("media"), item["title"]),
                tags_json=json.dumps(_tag_list(item.get("tags", [])), ensure_ascii=False),
                is_anonymous=False,
                status="published",
                llm_tags_json="[]",
            )
        )

    db.session.flush()
    managed_posts = CommunityPost.query.filter(CommunityPost.title.in_(managed_titles)).order_by(CommunityPost.id.asc()).all()
    if not managed_posts:
        db.session.commit()
        return

    comment_specs = [
        ("chenming", "学习行为数据看板：想找前端和产品同学一起把指标讲清楚", "这个指标体系适合做成老师端首页，我可以帮忙整理成汇报叙事。"),
        ("linke", "候选团队确认页原型：角色不是标签，应该允许学生表达不适配", "我可以把这个确认页做成高保真，顺便考虑移动端展示。"),
        ("zhangsan", "大模型画像解析的边界：建议保留规则评分作为兜底", "同意，规则兜底很重要，不然课堂网络波动时也不影响分组。"),
        ("jiangran", "建议每个任务都设置验收标准和风险备注", "验收标准可以做成任务模板字段，我愿意一起整理。"),
        ("tangyue", "预沟通期可以设计成 24 小时内完成的小型协商", "24 小时确认期很适合课堂节奏，也方便老师统一推进。"),
    ]
    posts_by_title = {post.title: post for post in managed_posts}
    for account, title, content in comment_specs:
        user = users_by_account.get(account)
        post = posts_by_title.get(title)
        if not user or not post:
            continue
        exists = PostComment.query.filter_by(post_id=post.id, user_id=user.id, content=content).first()
        if not exists:
            db.session.add(PostComment(post_id=post.id, user_id=user.id, content=content))

    for idx, post in enumerate(managed_posts):
        if len(students) < 2:
            continue
        for offset in range(1, min(5, len(students))):
            user = students[(idx + offset) % len(students)]
            exists = PostInteraction.query.filter_by(user_id=user.id, post_id=post.id, type="post_like").first()
            if not exists:
                db.session.add(PostInteraction(user_id=user.id, post_id=post.id, type="post_like"))
        favorite_user = students[(idx + 5) % len(students)]
        exists = PostInteraction.query.filter_by(user_id=favorite_user.id, post_id=post.id, type="post_favorite").first()
        if not exists:
            db.session.add(PostInteraction(user_id=favorite_user.id, post_id=post.id, type="post_favorite"))

    db.session.commit()


def _load_class_roster_names():
    """加载班级演示学生真实姓名与简介（database/seeds/class_roster_names.json）。"""
    import json
    from pathlib import Path

    seed_path = Path(__file__).resolve().parents[2] / "database" / "seeds" / "class_roster_names.json"
    if seed_path.is_file():
        return json.loads(seed_path.read_text(encoding="utf-8"))
    return {}


def _seed_demo_classes():
    """首次运行时初始化大学班级、演示学生与画像."""
    import json

    import bcrypt

    from app.models import ClassMembership, Classroom, User, UserProfile

    if Classroom.query.first():
        return

    roster_names = _load_class_roster_names()
    password_hash = bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode()
    admin = User.query.filter_by(role="admin").first()
    class_specs = [
        ("人工智能 2401 班", "AI2401", "人工智能", "2024", "AI 产品创新实践", "ai2401"),
        ("软件工程 2402 班", "SE2402", "软件工程", "2024", "软件工程综合实训", "se2402"),
        ("数据科学 2301 班", "DS2301", "数据科学与大数据技术", "2023", "数据智能项目实践", "ds2301"),
        ("数字媒体技术 2401 班", "DM2401", "数字媒体技术", "2024", "交互媒体设计实践", "dm2401"),
    ]
    role_cycle = ["技术开发", "产品设计", "数据支持", "文档汇报", "协调对接", "测试验证"]
    skill_cycle = ["Python", "前端开发", "数据分析", "UI设计", "项目管理", "后端开发"]
    for class_name, code, major, grade, course, prefix in class_specs:
        cls = Classroom(
            name=class_name,
            code=code,
            major=major,
            grade=grade,
            course_name=course,
            teacher_id=admin.id if admin else None,
            max_students=20,
            status="active",
            description=f"{course} 演示班级，用于班级管理、审批和均衡分组。",
        )
        db.session.add(cls)
        db.session.flush()
        prefix_roster = roster_names.get(prefix) or []
        headline_tpl = f"{major} · {grade}级本科生"
        for i in range(1, 13):
            account = f"{prefix}_{i:02d}"
            roster_item = prefix_roster[i - 1] if i - 1 < len(prefix_roster) else {}
            display_name = roster_item.get("name") or f"学生{i:02d}"
            display_bio = roster_item.get("bio") or f"{major}专业在读，参与{course}课程项目协作。"
            display_interest = roster_item.get("research_interest") or course
            user = User.query.filter_by(account=account).first()
            if not user:
                user = User(
                    name=display_name,
                    account=account,
                    password_hash=password_hash,
                    role="user",
                    headline=headline_tpl,
                    bio=display_bio,
                    research_interest=display_interest,
                )
                db.session.add(user)
                db.session.flush()
            role = role_cycle[(i - 1) % len(role_cycle)]
            skill = skill_cycle[(i - 1) % len(skill_cycle)]
            if not UserProfile.query.filter_by(user_id=user.id).first():
                db.session.add(
                    UserProfile(
                        user_id=user.id,
                        major=major,
                        pref_role=role,
                        knowledge_score=6 + (i % 4),
                        skill_score=6 + ((i + 1) % 4),
                        collab_score=6 + ((i + 2) % 4),
                        active_tags_json=json.dumps(
                            [
                                {"name": skill, "dimension": "skill"},
                                {"name": role, "dimension": "collab"},
                                {"name": major, "dimension": "knowledge"},
                            ],
                            ensure_ascii=False,
                        ),
                        passive_tags_json="[]",
                    )
                )
            db.session.add(
                ClassMembership(
                    class_id=cls.id,
                    user_id=user.id,
                    status="active",
                    source="demo_seed",
                    joined_at=__import__("datetime").datetime.utcnow(),
                )
            )
    db.session.commit()


def _seed_demo_activities():
    """初始化班级归属明确的组队活动，并为部分学生预置参与记录."""
    import json

    from app.models import ClassMembership, Classroom, TeamActivity, TeamActivityParticipant, TeamRoom, User, UserProfile

    classes = Classroom.query.filter_by(status="active").order_by(Classroom.create_time.asc()).all()
    if not classes:
        return

    fallback_class = classes[0]
    unscoped = TeamActivity.query.filter(TeamActivity.class_id.is_(None)).all()
    for activity in unscoped:
        activity.class_id = fallback_class.id
        if not activity.course_name:
            activity.course_name = fallback_class.course_name

    admin = User.query.filter_by(role="admin").first()
    activity_specs = [
        ("第 4 周产品原型项目组队", "task_auto", "collecting", 4, "完成一个可演示的 AI 产品低保真原型", ["产品设计", "UI设计", "前端开发"]),
        ("第二学期课程设计", "task_auto", "draft", 4, "围绕课程主题完成需求分析、开发实现与展示汇报", ["Python", "后端开发", "文档汇报"]),
        ("期末展示自由组队", "free_team", "collecting", 4, "学生自由发起队伍，老师最后锁定组队结果", ["项目管理", "协调对接", "文档汇报"]),
        ("数据可视化专题项目", "task_auto", "collecting", 3, "基于真实数据集完成分析、可视化和结论表达", ["数据分析", "Python", "文档汇报"]),
        ("交互媒体创意工作坊", "free_team", "collecting", 4, "自由组队完成交互叙事或媒体装置方案", ["UI设计", "前端开发", "主动沟通"]),
    ]

    for idx, cls in enumerate(classes):
        primary = activity_specs[idx % len(activity_specs)]
        secondary = activity_specs[(idx + 2) % len(activity_specs)]
        for title, mode, status, group_size, goal, tags in (primary, secondary):
            scoped_title = f"{cls.name}｜{title}"
            activity = TeamActivity.query.filter_by(title=scoped_title).first()
            if not activity:
                activity = TeamActivity(
                    title=scoped_title,
                    description=f"{cls.name} 专属活动，学生只在本班范围内参与。",
                    course_name=cls.course_name,
                    mode=mode,
                    status=status,
                    group_size=group_size,
                    task_goal=goal,
                    required_tags_json=json.dumps(tags, ensure_ascii=False),
                    required_roles_json=json.dumps(["技术开发", "产品设计", "文档汇报"], ensure_ascii=False),
                    class_id=cls.id,
                    created_by=admin.id if admin else None,
                )
                db.session.add(activity)
                db.session.flush()
            members = (
                ClassMembership.query.filter_by(class_id=cls.id, status="active")
                .order_by(ClassMembership.create_time.asc())
                .limit(8 if status != "draft" else 4)
                .all()
            )
            for member in members:
                if TeamActivityParticipant.query.filter_by(activity_id=activity.id, user_id=member.user_id).first():
                    continue
                prof = UserProfile.query.filter_by(user_id=member.user_id).order_by(UserProfile.create_time.desc()).first()
                db.session.add(
                    TeamActivityParticipant(
                        activity_id=activity.id,
                        user_id=member.user_id,
                        status="joined",
                        active_tags_json=prof.active_tags_json if prof else "[]",
                        passive_tags_json=prof.passive_tags_json if prof else "[]",
                        profile_snapshot_json=json.dumps(prof.to_dict(), ensure_ascii=False) if prof else "{}",
                    )
                )
            if mode == "free_team":
                first_members = [m.user_id for m in members[:3]]
                if first_members and not TeamRoom.query.filter_by(activity_id=activity.id).first():
                    room = TeamRoom(
                        activity_id=activity.id,
                        name=f"{cls.code or cls.name} A 队",
                        description="演示自由组队队伍，学生可申请加入或后续锁定。",
                        leader_id=first_members[0],
                        desired_tags_json=json.dumps(tags[:2], ensure_ascii=False),
                        status="open",
                    )
                    room.set_member_ids(first_members)
                    db.session.add(room)
    db.session.commit()


def _seed_demo_enrichment():
    """演示：时间轴多样状态、Rubric、里程碑、首班健康叙事."""
    import json
    from datetime import datetime, timedelta

    from app.models import Classroom, Milestone, Rubric, TeamActivity
    from app.services.classroom_insights import save_timeline

    cls = Classroom.query.filter_by(status="active").order_by(Classroom.create_time.asc()).first()
    if not cls:
        return
    timeline = [
        {"key": "profile", "title": "画像采集", "hint": "学生完成标签与自述", "offset_days": 0, "status": "done", "due_at": (datetime.utcnow() - timedelta(days=14)).date().isoformat()},
        {"key": "grouping", "title": "组队确认", "hint": "发布活动并完成预沟通", "offset_days": 7, "status": "active", "due_at": (datetime.utcnow() + timedelta(days=3)).date().isoformat()},
        {"key": "midterm", "title": "中期检查", "hint": "查看任务进度与风险", "offset_days": 21, "status": "pending", "due_at": (datetime.utcnow() + timedelta(days=18)).date().isoformat()},
        {"key": "final", "title": "期末展示", "hint": "导出过程评价与团队报告", "offset_days": 42, "status": "pending", "due_at": (datetime.utcnow() + timedelta(days=35)).date().isoformat()},
    ]
    save_timeline(cls, timeline)
    if not Rubric.query.filter_by(class_id=cls.id).first():
        db.session.add(
            Rubric(
                class_id=cls.id,
                title="项目过程评价量表（演示）",
                criteria_json=json.dumps(
                    [
                        {"key": "contribution", "label": "贡献度", "max": 5},
                        {"key": "collaboration", "label": "协作沟通", "max": 5},
                        {"key": "quality", "label": "交付质量", "max": 5},
                    ],
                    ensure_ascii=False,
                ),
            )
        )
    act = TeamActivity.query.filter_by(class_id=cls.id, mode="task_auto").filter(
        TeamActivity.status.in_(["collecting", "grouping", "preview"])
    ).first()
    if act and not Milestone.query.filter_by(activity_id=act.id).first():
        due1 = datetime.utcnow() + timedelta(days=7)
        due2 = datetime.utcnow() + timedelta(days=21)
        db.session.add(Milestone(activity_id=act.id, title="完成需求与原型", due_at=due1, status="active", sort_order=1))
        db.session.add(Milestone(activity_id=act.id, title="中期演示", due_at=due2, status="pending", sort_order=2))
    db.session.commit()
