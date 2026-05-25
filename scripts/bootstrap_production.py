#!/usr/bin/env python3
"""生产环境首次初始化：创建首个管理员账号（空库时）."""
from __future__ import annotations

import argparse
import getpass
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import bcrypt

from app import create_app, db
from app.models import User, UserSubscription


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _account_from_email(email: str) -> str:
    local = email.split("@", 1)[0].lower()
    safe = re.sub(r"[^a-z0-9_]", "_", local)[:32] or "admin"
    base = safe
    n = 1
    while User.query.filter_by(account=base).first():
        n += 1
        base = f"{safe}_{n}"
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description="生产环境 bootstrap：创建首个管理员")
    parser.add_argument("--email", help="管理员邮箱（或 TEAMMIND_BOOTSTRAP_ADMIN_EMAIL）")
    parser.add_argument("--password", help="管理员密码（或 TEAMMIND_BOOTSTRAP_ADMIN_PASSWORD）")
    parser.add_argument("--name", default="系统管理员", help="显示名称")
    parser.add_argument("--force", action="store_true", help="已有 admin 时仍创建新账号（不推荐）")
    args = parser.parse_args()

    email = (args.email or os.environ.get("TEAMMIND_BOOTSTRAP_ADMIN_EMAIL") or "").strip().lower()
    password = args.password or os.environ.get("TEAMMIND_BOOTSTRAP_ADMIN_PASSWORD") or ""

    if not email:
        email = input("管理员邮箱: ").strip().lower()
    if not _valid_email(email):
        print("请提供有效邮箱", file=sys.stderr)
        return 1
    if not password:
        password = getpass.getpass("管理员密码（至少 8 位，含字母与数字）: ")
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        print("密码至少 8 位且包含字母与数字", file=sys.stderr)
        return 1

    app = create_app()
    with app.app_context():
        existing_admin = User.query.filter_by(role="admin").first()
        if existing_admin and not args.force:
            print(f"已有管理员账号: {existing_admin.account} (id={existing_admin.id})，无需 bootstrap")
            return 0

        if User.query.filter_by(email=email).first():
            print(f"邮箱 {email} 已被使用", file=sys.stderr)
            return 1

        account = _account_from_email(email)
        user = User(
            name=args.name.strip() or "系统管理员",
            account=account,
            email=email,
            password_hash=hash_pw(password),
            role="admin",
            is_demo=False,
            status="active",
            email_verified_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.flush()
        if not UserSubscription.query.filter_by(user_id=user.id).first():
            db.session.add(UserSubscription(user_id=user.id, plan_code="free", status="active"))
        db.session.commit()
        print(f"已创建管理员: account={account}, email={email}, id={user.id}")
        print("请使用邮箱或账号登录教师端 /admin/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
