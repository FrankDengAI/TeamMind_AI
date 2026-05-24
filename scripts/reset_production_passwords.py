#!/usr/bin/env python3
"""公网部署后重置演示账号密码（生产安全加固）."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import bcrypt

from app import create_app, db
from app.models import User

DEFAULT_DEMO_ACCOUNTS = ("admin", "teacher", "zhangsan")


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="重置 TeamMind AI 演示账号密码")
    parser.add_argument("--admin-password", help="admin / teacher 新密码（至少 6 位）")
    parser.add_argument("--student-password", help="演示学生账号新密码（至少 6 位）")
    parser.add_argument("--include-students", action="store_true", help="同时重置所有 role=user 的演示账号")
    parser.add_argument("--yes", action="store_true", help="跳过确认提示")
    args = parser.parse_args()

    admin_pw = args.admin_password or getpass.getpass("管理员/教师新密码: ")
    if len(admin_pw) < 6:
        print("密码至少 6 位", file=sys.stderr)
        return 1

    student_pw = args.student_password
    if args.include_students:
        student_pw = student_pw or getpass.getpass("演示学生新密码: ")
        if len(student_pw) < 6:
            print("学生密码至少 6 位", file=sys.stderr)
            return 1

    if not args.yes:
        confirm = input("确认重置演示账号密码？[y/N] ").strip().lower()
        if confirm not in {"y", "yes"}:
            print("已取消")
            return 0

    app = create_app()
    with app.app_context():
        updated: list[str] = []
        for account in DEFAULT_DEMO_ACCOUNTS:
            user = User.query.filter_by(account=account).first()
            if user:
                user.password_hash = hash_pw(admin_pw)
                updated.append(account)

        if args.include_students:
            for user in User.query.filter_by(role="user").all():
                user.password_hash = hash_pw(student_pw)
                updated.append(user.account)

        if not updated:
            print("未找到可重置的账号。请先确保数据库已初始化。")
            return 1

        db.session.commit()
        print(f"已重置 {len(updated)} 个账号密码。")
        if not args.include_students:
            print("提示：演示学生账号仍为默认密码，可使用 --include-students 一并重置。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
