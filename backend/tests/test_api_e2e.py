"""API 端到端测试."""
import json

import bcrypt

from app import db
from app.models import ClassMembership, Classroom, CommunityPost, GroupInfo, PostInteraction, Task, User, UserProfile
from app.services.class_grouping import suggest_group_sizes


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_login_and_profile(client):
    r = client.post("/api/auth/login", json={"account": "pytest_user", "password": "test123"})
    assert r.status_code == 200
    token = r.json["token"]
    headers = {"Authorization": f"Bearer {token}"}
    text = (
        "计算机专业学生，掌握Python、Java、MySQL，擅长后端开发与软件工程，"
        "团队合作中担任技术开发，沟通能力强，风格积极主动严谨细致。"
    ) * 2
    r2 = client.post("/api/profile/parse", json={"raw_text": text}, headers=headers)
    assert r2.status_code == 200
    assert "profile" in r2.json


def test_update_me_and_change_password(client):
    headers = _token(client, "pytest_user")
    updated = client.put(
        "/api/auth/me",
        json={"name": "New Name", "avatar_url": "https://example.com/avatar.png", "bio": "喜欢项目协作"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json["name"] == "New Name"
    assert updated.json["avatar_url"].endswith("avatar.png")

    changed = client.post(
        "/api/auth/change-password",
        json={"old_password": "test123", "new_password": "newpass123"},
        headers=headers,
    )
    assert changed.status_code == 200
    relogin = client.post("/api/auth/login", json={"account": "pytest_user", "password": "newpass123"})
    assert relogin.status_code == 200


def _token(client, account):
    r = client.post("/api/auth/login", json={"account": account, "password": "test123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json['token']}"}


def _seed_user_with_profile(account, name, role="技术开发"):
    pw = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
    user = User(name=name, account=account, password_hash=pw, role="user")
    db.session.add(user)
    db.session.flush()
    profile = UserProfile(
        user_id=user.id,
        major="计算机",
        pref_role=role,
        knowledge_score=7,
        skill_score=8,
        collab_score=7,
        active_tags_json=json.dumps([{"name": "Python", "dimension": "skill"}, {"name": role, "dimension": "collab"}], ensure_ascii=False),
        passive_tags_json="[]",
    )
    db.session.add(profile)
    db.session.commit()
    return user


def _seed_class_with_members(code, *accounts):
    cls = Classroom.query.filter_by(code=code).first()
    if not cls:
        admin = User.query.filter_by(account="pytest_admin").first()
        cls = Classroom(
            name=f"测试班级 {code}",
            code=code,
            major="测试专业",
            grade="2026",
            course_name="测试课程设计",
            teacher_id=admin.id if admin else None,
            max_students=20,
            status="active",
        )
        db.session.add(cls)
        db.session.flush()
    for account in accounts:
        user = User.query.filter_by(account=account).first()
        if user and not ClassMembership.query.filter_by(class_id=cls.id, user_id=user.id).first():
            db.session.add(ClassMembership(class_id=cls.id, user_id=user.id, status="active", source="pytest"))
    db.session.commit()
    return cls.id


def test_team_activity_auto_group_flow(client, app):
    with app.app_context():
        base = User.query.filter_by(account="pytest_user").first()
        db.session.add(
            UserProfile(
                user_id=base.id,
                major="设计",
                pref_role="设计执行",
                knowledge_score=6,
                skill_score=7,
                collab_score=8,
                active_tags_json=json.dumps([{"name": "UI设计", "dimension": "skill"}, {"name": "设计执行", "dimension": "collab"}], ensure_ascii=False),
                passive_tags_json="[]",
            )
        )
        _seed_user_with_profile("pytest_user2", "User2", "技术开发")
        class_id = _seed_class_with_members("AUTO-FLOW", "pytest_user", "pytest_user2")

    admin_headers = _token(client, "pytest_admin")
    r = client.post(
        "/api/admin/team-activities",
        json={"title": "自动组队测试", "mode": "task_auto", "group_size": 2, "class_id": class_id, "task_goal": "完成 Python 原型", "required_tags": ["Python"]},
        headers=admin_headers,
    )
    assert r.status_code == 201
    activity_id = r.json["id"]
    assert client.post(f"/api/admin/team-activities/{activity_id}/publish-collect", headers=admin_headers).status_code == 200

    user1_headers = _token(client, "pytest_user")
    user2_headers = _token(client, "pytest_user2")
    assert client.post(f"/api/team-activities/{activity_id}/join", json={"active_tags": []}, headers=user1_headers).status_code == 200
    assert client.post(f"/api/team-activities/{activity_id}/join", json={"active_tags": []}, headers=user2_headers).status_code == 200

    grouped = client.post(f"/api/admin/team-activities/{activity_id}/auto-group", headers=admin_headers)
    assert grouped.status_code == 200
    assert grouped.json["groups"][0]["activity_id"] == activity_id
    assert client.post(f"/api/admin/team-activities/{activity_id}/publish-groups", headers=admin_headers).status_code == 200

    active = client.get("/api/team-activities/active", headers=user1_headers)
    assert active.status_code == 200
    mine = next(a for a in active.json if a["id"] == activity_id)
    assert mine["my_participant"]["status"] == "joined"
    assert mine["my_group"]["activity_id"] == activity_id


def test_free_team_request_and_lock(client, app):
    with app.app_context():
        _seed_user_with_profile("pytest_free2", "Free2", "数据支持")
        class_id = _seed_class_with_members("FREE-FLOW", "pytest_user", "pytest_free2")

    admin_headers = _token(client, "pytest_admin")
    leader_headers = _token(client, "pytest_user")
    member_headers = _token(client, "pytest_free2")
    r = client.post(
        "/api/admin/team-activities",
        json={"title": "自由组队测试", "mode": "free_team", "group_size": 2, "class_id": class_id, "task_goal": "自选主题组队"},
        headers=admin_headers,
    )
    activity_id = r.json["id"]
    assert client.post(f"/api/admin/team-activities/{activity_id}/publish-collect", headers=admin_headers).status_code == 200
    client.post(f"/api/team-activities/{activity_id}/join", json={"active_tags": []}, headers=leader_headers)
    client.post(f"/api/team-activities/{activity_id}/join", json={"active_tags": []}, headers=member_headers)

    room = client.post(f"/api/team-activities/{activity_id}/teams", json={"name": "自由 A 队"}, headers=leader_headers)
    assert room.status_code == 201
    room_id = room.json["id"]
    req = client.post(f"/api/team-activities/{activity_id}/teams/{room_id}/join-request", json={"message": "想加入"}, headers=member_headers)
    assert req.status_code == 200
    approved = client.post(f"/api/team-activities/{activity_id}/requests/{req.json['id']}/approve", headers=leader_headers)
    assert approved.status_code == 200
    assert len(approved.json["member_ids"]) == 2
    locked = client.post(f"/api/admin/team-activities/{activity_id}/lock-free-teams", headers=admin_headers)
    assert locked.status_code == 200
    assert locked.json["groups"][0]["activity_id"] == activity_id
    assert client.post(f"/api/team-activities/{activity_id}/teams", json={"name": "锁定后新队伍"}, headers=leader_headers).status_code == 400


def test_student_cannot_use_teacher_operations(client, app):
    user_headers = _token(client, "pytest_user")

    assert client.get("/api/export/profile", headers=user_headers).status_code == 403
    assert client.post("/api/group/create", json={"user_ids": [1, 2], "group_size": 2}, headers=user_headers).status_code == 403
    assert client.post("/api/task/assign", json={"group_id": 1}, headers=user_headers).status_code == 403
    assert client.post("/api/task/adjust", json={"group_id": 1}, headers=user_headers).status_code == 403
    assert client.post("/api/report/generate", json={"group_id": 1}, headers=user_headers).status_code == 403


def test_student_cannot_access_or_pollute_other_group(client, app):
    with app.app_context():
        other = _seed_user_with_profile("pytest_other_group", "OtherGroup", "数据支持")
        group = GroupInfo(group_name="Other Group", member_ids=json.dumps([other.id]), avg_knowledge=7, avg_skill=7, avg_collab=7)
        db.session.add(group)
        db.session.flush()
        task = Task(task_name="Other Task", group_id=group.id, assignee_id=other.id, difficulty=3, progress=0)
        db.session.add(task)
        db.session.commit()
        group_id = group.id
        task_id = task.id

    user_headers = _token(client, "pytest_user")
    assert client.get(f"/api/group/{group_id}", headers=user_headers).status_code == 403
    assert client.get(f"/api/report/{group_id}", headers=user_headers).status_code == 403
    polluted = client.post(
        "/api/behavior/log",
        json={"group_id": group_id, "task_id": task_id, "progress": 80, "event_type": "manual"},
        headers=user_headers,
    )
    assert polluted.status_code == 403


def test_student_task_visibility_and_self_create(client, app):
    with app.app_context():
        user = User.query.filter_by(account="pytest_user").first()
        teammate = _seed_user_with_profile("pytest_taskmate", "TaskMate", "数据支持")
        group = GroupInfo(group_name="Task Visible Group", member_ids=json.dumps([user.id, teammate.id]), avg_knowledge=7, avg_skill=7, avg_collab=7)
        db.session.add(group)
        db.session.flush()
        teacher_task = Task(task_name="Teacher Assigned Task", group_id=group.id, assignee_id=teammate.id, difficulty=3, progress=0)
        db.session.add(teacher_task)
        db.session.commit()
        user_id = user.id
        group_id = group.id

    user_headers = _token(client, "pytest_user")

    groups = client.get("/api/group/list", headers=user_headers)
    assert groups.status_code == 200
    assert any(g["id"] == group_id for g in groups.json)

    personal = client.get("/api/board/personal", headers=user_headers)
    assert personal.status_code == 200
    assert any(t["task_name"] == "Teacher Assigned Task" for t in personal.json["team_tasks"])
    assert not any(t["task_name"] == "Teacher Assigned Task" for t in personal.json["tasks"])

    created = client.post(
        "/api/task/create",
        json={"group_id": group_id, "task_name": "Student Proposed Task", "description": "我想主动承担这项工作"},
        headers=user_headers,
    )
    assert created.status_code == 201
    assert created.json["assignee_id"] == user_id

    personal_after = client.get("/api/board/personal", headers=user_headers)
    assert any(t["task_name"] == "Student Proposed Task" for t in personal_after.json["tasks"])
    assert any(t["task_name"] == "Student Proposed Task" for t in personal_after.json["team_tasks"])


def test_task_assignment_preserves_dependencies(client, app):
    with app.app_context():
        user = User.query.filter_by(account="pytest_user").first()
        teammate = _seed_user_with_profile("pytest_dep_mate", "DepMate", "技术开发")
        if not UserProfile.query.filter_by(user_id=user.id).first():
            db.session.add(
                UserProfile(
                    user_id=user.id,
                    major="计算机",
                    pref_role="协调对接",
                    knowledge_score=7,
                    skill_score=7,
                    collab_score=7,
                    active_tags_json="[]",
                    passive_tags_json="[]",
                )
            )
        group = GroupInfo(group_name="Dependency Group", member_ids=json.dumps([user.id, teammate.id]), avg_knowledge=7, avg_skill=7, avg_collab=7)
        db.session.add(group)
        db.session.commit()
        group_id = group.id

    assigned = client.post(
        "/api/task/assign",
        json={
            "group_id": group_id,
            "custom_tasks": [
                {"name": "任务 A", "difficulty": 2, "role": "协调对接", "hours": 2, "depends": []},
                {"name": "任务 B", "difficulty": 3, "role": "技术开发", "hours": 3, "depends": [0]},
            ],
        },
        headers=_token(client, "pytest_admin"),
    )
    assert assigned.status_code == 200
    tasks = assigned.json["tasks"]
    assert tasks[1]["depends_on"] == [tasks[0]["id"]]


def test_chat_and_community_visibility_guards(client, app):
    user_headers = _token(client, "pytest_user")
    ghost_chat = client.post("/api/chat/conversations", json={"target_user_id": 999999}, headers=user_headers)
    assert ghost_chat.status_code == 404

    with app.app_context():
        user = User.query.filter_by(account="pytest_user").first()
        hidden = CommunityPost(user_id=user.id, title="Hidden", content="这是一条被隐藏的帖子内容", status="hidden")
        db.session.add(hidden)
        db.session.commit()
        post_id = hidden.id

    assert client.post(f"/api/community/posts/{post_id}/like", headers=user_headers).status_code == 404
    assert client.post(f"/api/community/posts/{post_id}/favorite", headers=user_headers).status_code == 404
    assert client.post(f"/api/community/posts/{post_id}/comment", json={"content": "不应评论隐藏内容"}, headers=user_headers).status_code == 404


def test_community_json_and_interaction_idempotency(client, app):
    user_headers = _token(client, "pytest_user")
    invalid = client.post(
        "/api/community/posts",
        data={"content": "这是一条格式错误标签测试内容", "tags": "[not-json"},
        headers=user_headers,
    )
    assert invalid.status_code == 400

    with app.app_context():
        user = User.query.filter_by(account="pytest_user").first()
        post = CommunityPost(user_id=user.id, title="可互动帖子", content="这是一条可互动的帖子内容", tags_json="[]", status="published")
        db.session.add(post)
        db.session.commit()
        post_id = post.id

    first_like = client.post(f"/api/community/posts/{post_id}/like", headers=user_headers)
    second_like = client.post(f"/api/community/posts/{post_id}/like", headers=user_headers)
    first_favorite = client.post(f"/api/community/posts/{post_id}/favorite", headers=user_headers)
    second_favorite = client.post(f"/api/community/posts/{post_id}/favorite", headers=user_headers)
    assert first_like.status_code == second_like.status_code == 200
    assert first_favorite.status_code == second_favorite.status_code == 200
    assert second_like.json["stats"]["likes"] == 1
    assert second_favorite.json["stats"]["favorites"] == 1
    with app.app_context():
        assert PostInteraction.query.filter_by(post_id=post_id, type="post_like").count() == 1
        assert PostInteraction.query.filter_by(post_id=post_id, type="post_favorite").count() == 1


def test_classroom_join_leave_and_member_management(client, app):
    admin_headers = _token(client, "pytest_admin")
    user_headers = _token(client, "pytest_user")

    created = client.post(
        "/api/admin/classes",
        json={"name": "软件工程测试班", "code": "T-SE-01", "major": "软件工程", "course_name": "项目实践", "max_students": 20},
        headers=admin_headers,
    )
    assert created.status_code == 201
    class_id = created.json["id"]

    join = client.post(f"/api/classes/{class_id}/join-request", json={"message": "我是本课程学生"}, headers=user_headers)
    assert join.status_code == 201
    listed = client.get("/api/admin/classes", headers=admin_headers)
    assert next(c for c in listed.json if c["id"] == class_id)["pending_count"] == 1

    approved = client.post(f"/api/admin/classes/{class_id}/requests/{join.json['id']}/approve", headers=admin_headers)
    assert approved.status_code == 200
    assert approved.json["member_count"] == 1
    assert approved.json["members"][0]["user"]["account"] == "pytest_user"

    leave = client.post(f"/api/classes/{class_id}/leave-request", json={"message": "课程调整"}, headers=user_headers)
    assert leave.status_code == 201
    approved_leave = client.post(f"/api/admin/classes/{class_id}/requests/{leave.json['id']}/approve", headers=admin_headers)
    assert approved_leave.status_code == 200
    assert approved_leave.json["member_count"] == 0

    with app.app_context():
        teammate = _seed_user_with_profile("pytest_class_direct", "ClassDirect", "技术开发")
        teammate_id = teammate.id
    added = client.post(f"/api/admin/classes/{class_id}/members", json={"user_ids": [teammate_id]}, headers=admin_headers)
    assert added.status_code == 200
    assert added.json["member_count"] == 1
    removed = client.delete(f"/api/admin/classes/{class_id}/members/{teammate_id}", headers=admin_headers)
    assert removed.status_code == 200
    assert removed.json["member_count"] == 0


def test_class_grouping_advice_and_activity_scope(client, app):
    assert suggest_group_sizes(10, 4) == [4, 3, 3]
    assert suggest_group_sizes(12, 4) == [4, 4, 4]
    assert suggest_group_sizes(16, 4) == [4, 4, 4, 4]
    assert max(suggest_group_sizes(18, 4)) - min(suggest_group_sizes(18, 4)) <= 1

    with app.app_context():
        base = User.query.filter_by(account="pytest_user").first()
        if not UserProfile.query.filter_by(user_id=base.id).first():
            db.session.add(
                UserProfile(
                    user_id=base.id,
                    major="人工智能",
                    pref_role="技术开发",
                    knowledge_score=7,
                    skill_score=8,
                    collab_score=7,
                    active_tags_json=json.dumps([{"name": "Python", "dimension": "skill"}], ensure_ascii=False),
                    passive_tags_json="[]",
                )
            )
            db.session.flush()
        users = [
            base,
            _seed_user_with_profile("pytest_class_a", "ClassA", "技术开发"),
            _seed_user_with_profile("pytest_class_b", "ClassB", "数据支持"),
            _seed_user_with_profile("pytest_class_c", "ClassC", "文档汇报"),
        ]
        outsider = _seed_user_with_profile("pytest_class_out", "ClassOut", "产品设计")
        cls = Classroom(name="人工智能测试班", code="T-AI-01", major="人工智能", course_name="AI 实践", status="active", max_students=20)
        db.session.add(cls)
        db.session.flush()
        for u in users:
            db.session.add(ClassMembership(class_id=cls.id, user_id=u.id, status="active", source="pytest"))
        db.session.commit()
        class_id = cls.id
        allowed_ids = {u.id for u in users}

    admin_headers = _token(client, "pytest_admin")
    outsider_headers = _token(client, "pytest_class_out")
    activity = client.post(
        "/api/admin/team-activities",
        json={"title": "班级范围组队", "mode": "task_auto", "group_size": 2, "class_id": class_id, "task_goal": "完成 AI 原型"},
        headers=admin_headers,
    )
    assert activity.status_code == 201
    activity_id = activity.json["id"]
    assert client.post(f"/api/admin/team-activities/{activity_id}/publish-collect", headers=admin_headers).status_code == 200
    assert client.post(f"/api/team-activities/{activity_id}/join", json={"active_tags": []}, headers=outsider_headers).status_code == 403

    advice = client.get(f"/api/admin/classes/{class_id}/grouping-advice", headers=admin_headers)
    assert advice.status_code == 200
    assert advice.json["ai_analysis"]["summary"]

    class_detail = client.get(f"/api/admin/classes/{class_id}", headers=admin_headers)
    assert class_detail.status_code == 200
    assert any(a["id"] == activity_id for a in class_detail.json["activities"])

    student_created = client.post(
        f"/api/classes/{class_id}/activities",
        json={"title": "学生发起班级活动", "mode": "free_team", "group_size": 2, "task_goal": "同班自由组队"},
        headers=_token(client, "pytest_user"),
    )
    assert student_created.status_code == 201
    assert student_created.json["class_id"] == class_id
    assert student_created.json["status"] == "collecting"
    class_activities = client.get(f"/api/classes/{class_id}/activities", headers=_token(client, "pytest_user"))
    assert any(a["title"] == "学生发起班级活动" for a in class_activities.json)
    assert client.post(
        f"/api/classes/{class_id}/activities",
        json={"title": "班外活动", "mode": "free_team"},
        headers=outsider_headers,
    ).status_code == 403

    grouped = client.post(f"/api/admin/team-activities/{activity_id}/auto-group", headers=admin_headers)
    assert grouped.status_code == 200
    assert grouped.json["ai_analysis"]["summary"]
    grouped_ids = {mid for g in grouped.json["groups"] for mid in g["member_ids"]}
    assert grouped_ids == allowed_ids
    assert all(len(g["member_ids"]) == 2 for g in grouped.json["groups"])
    assert all(g["ai_analysis"]["summary"] for g in grouped.json["groups"])


def test_account_register_and_login(client):
    reg = client.post(
        "/api/auth/register",
        json={"name": "新用户", "account": "newuser01", "password": "Passw0rd1"},
    )
    assert reg.status_code == 201
    assert reg.json["user"]["account"] == "newuser01"
    login = client.post("/api/auth/login", json={"account": "newuser01", "password": "Passw0rd1"})
    assert login.status_code == 200


def test_email_auth_disabled(client):
    send = client.post("/api/auth/email/send-code", json={"email": "x@y.com", "purpose": "register"})
    assert send.status_code == 403
    reg = client.post(
        "/api/auth/register/email",
        json={"email": "x@y.com", "name": "X", "code": "123456", "password": "Passw0rd1"},
    )
    assert reg.status_code == 403


def test_ops_create_groups_requires_class_or_users(client):
    admin_headers = _token(client, "pytest_admin")
    empty = client.post("/api/admin/ops/create-groups", json={"group_size": 2}, headers=admin_headers)
    assert empty.status_code == 400


def test_student_cannot_access_admin_overview(client):
    headers = _token(client, "pytest_user")
    assert client.get("/api/admin/overview", headers=headers).status_code == 403


def test_teacher_cannot_manage_other_teacher_class(client, app):
    with app.app_context():
        pw = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
        admin_a = User.query.filter_by(account="pytest_admin").first()
        admin_b = User(name="Admin B", account="pytest_admin_b", password_hash=pw, role="admin")
        db.session.add(admin_b)
        db.session.flush()
        cls_a = Classroom(name="班A", code="ISO-A", teacher_id=admin_a.id, status="active")
        cls_b = Classroom(name="班B", code="ISO-B", teacher_id=admin_b.id, status="active")
        db.session.add_all([cls_a, cls_b])
        db.session.commit()
        id_a, id_b = cls_a.id, cls_b.id

    h_a = _token(client, "pytest_admin")
    h_b = _token(client, "pytest_admin_b")
    assert client.get(f"/api/admin/classes/{id_b}", headers=h_a).status_code == 403
    assert client.get(f"/api/admin/classes/{id_a}", headers=h_b).status_code == 403


def test_demo_user_cannot_join_real_class(client, app):
    with app.app_context():
        pw = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
        demo = User(name="Demo", account="pytest_demo", password_hash=pw, role="user", is_demo=True)
        db.session.add(demo)
        db.session.flush()
        admin = User.query.filter_by(account="pytest_admin").first()
        cls = Classroom(name="真实班", code="REAL-ISO", teacher_id=admin.id, status="active")
        db.session.add(cls)
        db.session.commit()
        class_id = cls.id

    demo_headers = _token(client, "pytest_demo")
    r = client.post(f"/api/classes/{class_id}/join-request", json={"message": "申请"}, headers=demo_headers)
    assert r.status_code == 400


def test_group_preview_filters_demo_user_ids(client, app):
    with app.app_context():
        pw = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
        demo = User(name="Demo2", account="pytest_demo2", password_hash=pw, role="user", is_demo=True)
        real = _seed_user_with_profile("pytest_real_grp", "Real", "设计执行")
        db.session.add(demo)
        db.session.commit()
        ids = [real.id, demo.id]

    admin_headers = _token(client, "pytest_admin")
    preview = client.post(
        "/api/group/preview",
        json={"user_ids": ids, "group_size": 2, "config": {"mode": "heterogeneous"}},
        headers=admin_headers,
    )
    assert preview.status_code == 400


def test_disabled_user_token_invalidated(client, app):
    headers = _token(client, "pytest_user")
    with app.app_context():
        from app.middleware.auth import bump_token_version

        user = User.query.filter_by(account="pytest_user").first()
        user.status = "disabled"
        bump_token_version(user)
        db.session.commit()

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code in (401, 403)
