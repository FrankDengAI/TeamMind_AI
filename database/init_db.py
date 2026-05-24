"""初始化 SQLite 数据库并导入种子数据."""
import json
import sys
from pathlib import Path

import bcrypt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app import create_app, db
from app.models import CommunityPost, GroupInfo, PostComment, PostInteraction, User, UserProfile

SEED_USERS = [
    ("管理员", "admin", "admin123", "admin"),
    ("张老师", "teacher", "admin123", "admin"),
]

SEEDS_DIR = ROOT / "database" / "seeds"


def load_seed_json(filename, default):
    path = SEEDS_DIR / filename
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


DEMO_STUDENTS = load_seed_json("demo_students.json", [])


def hash_pw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def _media(url: str, name: str = "课堂项目素材") -> str:
    return json.dumps([{"type": "image", "url": url, "name": name}], ensure_ascii=False)


def seed_posts(student_users):
    """种子社区内容：贴近真实大学/研究生项目协作。"""
    by_account = {item["account"]: user for user, item in student_users}
    posts = load_seed_json("demo_posts.json", [])
    created = []
    for item in posts:
        user = by_account[item["account"]]
        tags = [{"name": name, "dimension": dim} for name, dim in item["tags"]]
        post = CommunityPost(
            user_id=user.id,
            title=item["title"],
            content=item["content"],
            media_json=_media(item["media"], item["title"]),
            tags_json=json.dumps(tags, ensure_ascii=False),
            is_anonymous=False,
            status="published",
            llm_tags_json=json.dumps([], ensure_ascii=False),
        )
        db.session.add(post)
        db.session.flush()
        created.append(post)

    comments = [
        ("chenming", 0, "这个指标体系适合做成老师端首页，我可以帮忙整理成汇报叙事。"),
        ("linke", 1, "我可以把这个确认页做成高保真，顺便考虑移动端展示。"),
        ("zhangsan", 2, "同意，规则兜底很重要，不然课堂网络波动时就会卡住。"),
        ("jiangran", 6, "验收标准可以做成任务模板字段，我愿意一起整理。"),
        ("tangyue", 8, "24 小时确认期很适合课堂节奏，也方便老师统一推进。"),
    ]
    for account, post_idx, content in comments:
        if account in by_account and post_idx < len(created):
            db.session.add(PostComment(post_id=created[post_idx].id, user_id=by_account[account].id, content=content))

    for idx, post in enumerate(created):
        for account in list(by_account.keys())[idx % 5 : idx % 5 + 4]:
            db.session.add(PostInteraction(user_id=by_account[account].id, post_id=post.id, type="post_like"))
        if idx % 2 == 0 and "qianqi" in by_account:
            db.session.add(PostInteraction(user_id=by_account["qianqi"].id, post_id=post.id, type="post_favorite"))


def main():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        users = []
        for name, account, pwd, role in SEED_USERS:
            u = User(name=name, account=account, password_hash=hash_pw(pwd), role=role, bio="课程教师/管理员")
            db.session.add(u)
            users.append(u)

        student_users = []
        for item in DEMO_STUDENTS:
            u = User(
                name=item["name"],
                account=item["account"],
                password_hash=hash_pw("123456"),
                role="user",
                bio=item["bio"],
                headline=item.get("headline") or f"{item['major']} · 偏好{item['role']}",
                research_interest=item.get("research_interest") or " / ".join(item.get("industry", [])[:2]),
                availability=item.get("availability") or "每周 6-8 小时，可参与课程项目协作",
                display_theme=item.get("display_theme") or "aurora",
                avatar_url=f"https://api.dicebear.com/7.x/initials/svg?seed={item['account']}",
            )
            db.session.add(u)
            student_users.append((u, item))
            users.append(u)
        db.session.flush()

        for u, p in student_users:
            active_tags = [{"name": name, "dimension": dim} for name, dim in p["tags"]]
            score_breakdown = {
                "active": {"knowledge": p["ks"], "skill": p["ss"], "collab": p["cs"]},
                "llm": {"knowledge": 0, "skill": 0, "collab": 0},
                "passive": {"knowledge": 0, "skill": 0, "collab": 0},
                "task": {"knowledge": 0, "skill": 0, "collab": 0},
                "rule": {"knowledge": p["ks"], "skill": p["ss"], "collab": p["cs"]},
                "formula": "初始化演示画像：主动标签 + 专业背景 + 项目经验",
            }
            prof = UserProfile(
                user_id=u.id,
                identity=p["identity"],
                degree=p["degree"],
                field=p["field"],
                major=p["major"],
                theory_ability=json.dumps(p["theory"], ensure_ascii=False),
                knowledge_score=p["ks"],
                tech_skills=json.dumps(p["tech"], ensure_ascii=False),
                tool_skills=json.dumps(p["tools"], ensure_ascii=False),
                industry_skills=json.dumps(p["industry"], ensure_ascii=False),
                project_exp=json.dumps([], ensure_ascii=False),
                skill_score=p["ss"],
                comm_ability=p["comm"],
                pref_role=p["role"],
                collab_style=json.dumps(p["style"], ensure_ascii=False),
                team_exp=json.dumps({"team_count": 3, "role_history": [p["role"]]}, ensure_ascii=False),
                collab_score=p["cs"],
                active_tags_json=json.dumps(active_tags, ensure_ascii=False),
                passive_tags_json=json.dumps([], ensure_ascii=False),
                score_breakdown_json=json.dumps(score_breakdown, ensure_ascii=False),
                knowledge_final=p["ks"],
                skill_final=p["ss"],
                collab_final=p["cs"],
                raw_source="text",
            )
            db.session.add(prof)

        seed_posts(student_users)

        db.session.commit()
        print(f"数据库已初始化: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"共创建 {len(users)} 个用户，测试账号 admin/admin123")


if __name__ == "__main__":
    main()
