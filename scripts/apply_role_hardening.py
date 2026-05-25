#!/usr/bin/env python3
"""Apply role-hardening patches (UTF-8 safe)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def patch_admin() -> None:
    p = ROOT / "backend" / "app" / "api" / "admin.py"
    text = p.read_text(encoding="utf-8")
    if "teacher_classroom_query" not in text:
        text = text.replace(
            "from app.middleware.auth import admin_required, get_request_user_id, write_audit",
            "from app.middleware.auth import admin_required, bump_token_version, get_request_user_id, write_audit",
        )
        text = text.replace(
            "from app.models import AiUsageLog",
            "from app.models import AiUsageLog, Classroom",
        )
        text = text.replace(
            "from app.services.task_service import create_assigned_tasks",
            """from app.services.class_membership import filter_user_ids, restrict_to_class_members
from app.services.task_service import create_assigned_tasks
from app.services.teacher_scope import admin_owns_class, teacher_classroom_query""",
        )

    old_list = """@bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.all()
    data = []
    for u in users:"""
    new_list = """@bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    exclude_demo = request.args.get("exclude_demo", "1") in ("1", "true", "yes")
    include_demo = request.args.get("include_demo", "0") in ("1", "true", "yes")
    q = User.query
    if exclude_demo and not include_demo:
        q = q.filter((User.is_demo == False) | (User.is_demo.is_(None)))  # noqa: E712
    users = q.order_by(User.id.asc()).all()
    data = []
    for u in users:"""
    if old_list in text:
        text = text.replace(old_list, new_list)

    old_overview = """def overview():
    groups = GroupInfo.query.all()
    users = User.query.filter_by(role="user").count()
    profiles = UserProfile.query.count()"""
    new_overview = """def overview():
    uid = get_request_user_id()
    class_ids = [c.id for c in teacher_classroom_query(uid).all()]
    groups = GroupInfo.query.filter(GroupInfo.class_id.in_(class_ids)).all() if class_ids else []
    user_ids = set()
    for g in groups:
        user_ids.update(g.member_list())
    users = len([u for u in User.query.filter(User.id.in_(user_ids)).all() if u.role == "user" and not u.is_demo]) if user_ids else 0
    profiles = UserProfile.query.filter(UserProfile.user_id.in_(user_ids)).count() if user_ids else 0"""
    if old_overview in text:
        text = text.replace(old_overview, new_overview)

    old_dash = """def command_dashboard():
    \"\"\"指挥舱：全平台预警与项目组健康度.\"\"\"
    activity_id = request.args.get("activity_id", type=int)
    groups_q = GroupInfo.query
    if activity_id:
        groups_q = groups_q.filter_by(activity_id=activity_id)
    groups = groups_q.all()
    group_ids = [g.id for g in groups]
    tasks = Task.query.filter(Task.group_id.in_(group_ids)).all() if activity_id else Task.query.all()
    users = User.query.filter_by(role="user").all()
    profile_count = UserProfile.query.count()"""
    new_dash = """def command_dashboard():
    \"\"\"指挥舱：任课教师班级范围内的预警与项目组健康度.\"\"\"
    uid = get_request_user_id()
    class_ids = [c.id for c in teacher_classroom_query(uid).all()]
    activity_id = request.args.get("activity_id", type=int)
    groups_q = GroupInfo.query
    if class_ids:
        groups_q = groups_q.filter(GroupInfo.class_id.in_(class_ids))
    if activity_id:
        groups_q = groups_q.filter_by(activity_id=activity_id)
    groups = groups_q.all()
    group_ids = [g.id for g in groups]
    tasks = Task.query.filter(Task.group_id.in_(group_ids)).all() if group_ids else []
    member_ids = set()
    for g in groups:
        member_ids.update(g.member_list())
    users = User.query.filter(User.id.in_(member_ids), User.role == "user").all() if member_ids else []
    profile_count = UserProfile.query.filter(UserProfile.user_id.in_(member_ids)).count() if member_ids else 0"""
    if old_dash in text:
        text = text.replace(old_dash, new_dash)

    old_cls_loop = """        for cls in Classroom.query.order_by(Classroom.create_time.desc()).limit(8).all():"""
    new_cls_loop = """        for cls in teacher_classroom_query(uid).order_by(Classroom.create_time.desc()).limit(8).all():"""
    if old_cls_loop in text and "teacher_classroom_query(uid)" not in text.split("command_dashboard")[1][:2000]:
        text = text.replace(old_cls_loop, new_cls_loop, 1)
        # ensure uid in command_dashboard
        if "uid = get_request_user_id()" not in text.split("def command_dashboard")[1].split("class_summaries")[0]:
            text = text.replace(
                '    class_summaries = []\n    try:\n        from app.models import Classroom',
                '    class_summaries = []\n    uid = get_request_user_id()\n    try:\n        from app.models import Classroom',
                1,
            )

    old_ops = """    if not user_ids:
        users = User.query.filter_by(role="user").all()
        user_ids = [u.id for u in users]

    profiles = []"""
    new_ops = """    class_id = data.get("class_id")
    if class_id:
        user_ids = restrict_to_class_members(user_ids, int(class_id))
    else:
        user_ids = filter_user_ids(user_ids)
    if not user_ids:
        return jsonify({"error": "有效画像人数不足，无法分组"}), 400

    profiles = []"""
    if old_ops in text:
        text = text.replace(old_ops, new_ops)

    if '@bp.route("/users/<int:user_id>", methods=["PATCH"])' not in text:
        insert = '''

@bp.route("/users/<int:user_id>", methods=["PATCH"])
@admin_required
def patch_user(user_id):
    """禁用/启用用户或重置密码."""
    import bcrypt

    target = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    if data.get("status") in ("active", "disabled"):
        target.status = data["status"]
        bump_token_version(target)
    new_password = (data.get("password") or "").strip()
    if new_password:
        from app.services.auth_verification import validate_password_strength

        ok, msg = validate_password_strength(new_password)
        if not ok:
            return jsonify({"error": msg}), 400
        target.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        bump_token_version(target)
    db.session.commit()
    write_audit("admin_patch_user", "user", target.id, json.dumps({"status": target.status}, ensure_ascii=False))
    return jsonify({"user": target.to_dict()})


'''
        text = text.replace("@bp.route(\"/config\", methods=[\"GET\", \"PUT\"])", insert + '@bp.route("/config", methods=["GET", "PUT"])')

    p.write_text(text, encoding="utf-8")
    print("admin.py ok")


def patch_export() -> None:
    p = ROOT / "backend" / "app" / "api" / "export.py"
    text = p.read_text(encoding="utf-8")
    if "User.is_demo" not in text:
        text = text.replace("from app.models import GroupInfo", "from app.models import GroupInfo, User")
        text = text.replace(
            "        profiles = UserProfile.query.all()",
            "        profiles = UserProfile.query.join(User, User.id == UserProfile.user_id).filter(\n            (User.is_demo == False) | (User.is_demo.is_(None))\n        ).all()",
        )
        p.write_text(text, encoding="utf-8")
    print("export.py ok")


def patch_copilot() -> None:
    p = ROOT / "backend" / "app" / "api" / "copilot.py"
    text = p.read_text(encoding="utf-8")
    if "admin_owns_class" not in text:
        text = text.replace(
            "from app.models import Classroom",
            "from app.models import Classroom\nfrom app.services.teacher_scope import admin_owns_class",
        )
        text = text.replace(
            "    return cls.teacher_id == uid or cls.teacher_id is None",
            "    return admin_owns_class(cls, uid)",
        )
        text = text.replace(
            "    if cls.teacher_id and cls.teacher_id != uid:\n        return jsonify({\"error\": \"无权访问该班级\"}), 403",
            "    if not admin_owns_class(cls, uid):\n        return jsonify({\"error\": \"无权访问该班级\"}), 403",
        )
        p.write_text(text, encoding="utf-8")
    print("copilot.py ok")


def patch_chat() -> None:
    p = ROOT / "backend" / "app" / "api" / "chat.py"
    text = p.read_text(encoding="utf-8")
    if "users_share_active_class" not in text:
        text = text.replace(
            "from app.middleware.auth import decode_jwt_token, get_request_user_id",
            "from app.middleware.auth import decode_jwt_token, get_request_user_id\nfrom app.services.class_membership import users_share_active_class",
        )
        guard = '''
    user = User.query.get(uid)
    if not user or user.role != "admin":
        if not users_share_active_class(uid, target):
            return jsonify({"error": "仅可与同班学员私聊"}), 403
'''
        text = text.replace(
            "    if not User.query.get(target):\n        return jsonify",
            guard + "    if not User.query.get(target):\n        return jsonify",
            1,
        )
        text = text.replace(
            """def _save_message(conv: ChatConversation, sender_id: int, content: str, msg_type: str = "text") -> ChatMessage:
    content = (content or "").strip()
    if not content:
        raise ValueError""",
            """def _save_message(conv: ChatConversation, sender_id: int, content: str, msg_type: str = "text") -> ChatMessage:
    if conv.group_id is None:
        other = conv.user2_id if conv.user1_id == sender_id else conv.user1_id
        sender = User.query.get(sender_id)
        if not sender or sender.role != "admin":
            if not users_share_active_class(sender_id, other):
                raise ValueError("仅可与同班学员私聊")
    content = (content or "").strip()
    if not content:
        raise ValueError""",
        )
        text = text.replace(
            """            if uid not in conv.member_ids():
                return {"error":""",
            """            if uid not in conv.member_ids():
                return {"error": "无权访问"}
            if conv.group_id is None:
                other = conv.user2_id if conv.user1_id == uid else conv.user1_id
                user = User.query.get(uid)
                if not user or user.role != "admin":
                    if not users_share_active_class(uid, other):
                        return {"error": "仅可与同班学员私聊"}
            if False:
                return {"error":""",
        )
        p.write_text(text, encoding="utf-8")
    print("chat.py ok")


def patch_team_activity() -> None:
    p = ROOT / "backend" / "app" / "api" / "team_activity.py"
    text = p.read_text(encoding="utf-8")
    if "_admin_activity_guard" not in text:
        text = text.replace(
            "from app.services.tag_catalog import normalize_active_tags",
            """from app.services.tag_catalog import normalize_active_tags
from app.services.teacher_scope import admin_owns_class, teacher_classroom_query""",
        )
        helper = '''

def _admin_activity_guard(activity: TeamActivity, admin_id: int):
    if not activity.class_id:
        return None
    cls = Classroom.query.get(activity.class_id)
    if not admin_owns_class(cls, admin_id):
        return jsonify({"error": "无权操作该活动"}), 403
    return None


'''
        text = text.replace("admin_bp = Blueprint", helper + "admin_bp = Blueprint")
        text = text.replace(
            "        activities = TeamActivity.query.order_by(TeamActivity.create_time.desc()).all()",
            "        class_ids = [c.id for c in teacher_classroom_query(get_request_user_id()).all()]\n"
            "        activities = TeamActivity.query.filter(TeamActivity.class_id.in_(class_ids)).order_by(TeamActivity.create_time.desc()).all() if class_ids else []",
        )
        text = text.replace(
            "    classroom = Classroom.query.get(class_id)\n    if not classroom:\n        return jsonify",
            "    classroom = Classroom.query.get(class_id)\n    if not classroom:\n        return jsonify",
        )
        if "admin_owns_class(classroom, uid)" not in text:
            text = text.replace(
                "    if not classroom:\n        return jsonify({\"error\":",
                "    if not classroom:\n        return jsonify({\"error\":",
            )
            text = text.replace(
                """    classroom = Classroom.query.get(class_id)
    if not classroom:""",
                """    classroom = Classroom.query.get(class_id)
    if not classroom:""",
            )
            # insert ownership after classroom exists check
            text = text.replace(
                """    if not classroom:
        return jsonify({"error": """,
                """    if not classroom:
        return jsonify({"error": """,
                1,
            )
        # simpler insert after line 245
        marker = "    if not classroom:\n        return jsonify({\"error\": \""
        idx = text.find(marker)
        if idx > 0:
            end = text.find("), 404\n", idx)
            if end > 0:
                insert_at = end + len("), 404\n")
                own = "    if not admin_owns_class(classroom, uid):\n        return jsonify({\"error\": \"无权管理该班级\"}), 403\n"
                if own not in text:
                    text = text[:insert_at] + own + text[insert_at:]

        for fn in (
            "def admin_team_activity_detail",
            "def publish_collect",
            "def auto_group",
        ):
            pass
        # inject guard after get_or_404(activity_id) in admin routes
        import re

        def add_guard(m):
            body = m.group(0)
            if "_admin_activity_guard" in body:
                return body
            return (
                body
                + "\n    err = _admin_activity_guard(activity, get_request_user_id())\n    if err:\n        return err"
            )

        text = re.sub(
            r"(activity = TeamActivity\.query\.get_or_404\(activity_id\))\n",
            r"\1\n    err = _admin_activity_guard(activity, get_request_user_id())\n    if err:\n        return err\n",
            text,
        )
        p.write_text(text, encoding="utf-8")
    print("team_activity.py ok")


def main() -> int:
    patch_admin()
    patch_export()
    patch_copilot()
    patch_chat()
    patch_team_activity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
