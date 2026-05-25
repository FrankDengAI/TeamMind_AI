"""邮箱验证码签发与校验."""
from __future__ import annotations

import hashlib
import random
import re
from datetime import datetime, timedelta

import bcrypt
from flask import current_app

from app import db
from app.models import AuthToken, User
from app.services.email_service import is_valid_email, normalize_email, send_verification_email

CODE_TTL_MINUTES = 10
SEND_COOLDOWN_SECONDS = 60
DAILY_SEND_LIMIT = 10


def _hash_code(code: str) -> str:
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_code(code: str, code_hash: str) -> bool:
    return bcrypt.checkpw(code.encode("utf-8"), code_hash.encode("utf-8"))


def validate_account_name(account: str) -> str | None:
    """账号规则：3–32 位，字母数字下划线，不含 @。"""
    account = (account or "").strip()
    if len(account) < 3:
        return "账号至少 3 位"
    if len(account) > 32:
        return "账号不能超过 32 位"
    if "@" in account:
        return "请使用账号注册，不要使用邮箱格式"
    if not re.match(r"^[a-zA-Z0-9_]+$", account):
        return "账号仅支持字母、数字和下划线"
    return None


def validate_password_strength(password: str) -> str | None:
    if len(password) < 8:
        return "密码至少 8 位"
    if not re.search(r"[A-Za-z]", password):
        return "密码须包含字母"
    if not re.search(r"\d", password):
        return "密码须包含数字"
    return None


def account_from_email(email: str) -> str:
    local = email.split("@", 1)[0].lower()
    safe = re.sub(r"[^a-z0-9_]", "_", local)[:32] or "user"
    base = safe
    n = 1
    while User.query.filter_by(account=base).first():
        n += 1
        base = f"{safe}_{n}"
    return base


def _recent_send_count(email: str, since: datetime) -> int:
    return AuthToken.query.filter(
        AuthToken.email == email,
        AuthToken.create_time >= since,
    ).count()


def issue_email_code(email: str, purpose: str) -> None:
    """生成并发送验证码."""
    email = normalize_email(email)
    if not is_valid_email(email):
        raise ValueError("邮箱格式不正确")
    if purpose not in {"register", "reset_password"}:
        raise ValueError("无效的验证码用途")

    if purpose == "register":
        existing = User.query.filter_by(email=email).first()
        if existing and existing.email_verified_at:
            raise ValueError("该邮箱已注册")
    else:
        if not User.query.filter_by(email=email).first():
            raise ValueError("该邮箱未注册")

    now = datetime.utcnow()
    last = (
        AuthToken.query.filter_by(email=email, purpose=purpose)
        .order_by(AuthToken.create_time.desc())
        .first()
    )
    if last and last.create_time and (now - last.create_time).total_seconds() < SEND_COOLDOWN_SECONDS:
        raise ValueError("发送过于频繁，请稍后再试")

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if _recent_send_count(email, day_start) >= DAILY_SEND_LIMIT:
        raise ValueError("今日发送次数已达上限")

    code = f"{random.randint(0, 999999):06d}"
    row = AuthToken(
        email=email,
        purpose=purpose,
        code_hash=_hash_code(code),
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.session.add(row)
    db.session.commit()
    send_verification_email(email, code, purpose)


def verify_email_code(email: str, purpose: str, code: str) -> bool:
    email = normalize_email(email)
    code = (code or "").strip()
    if not code or len(code) != 6:
        return False
    now = datetime.utcnow()
    rows = (
        AuthToken.query.filter_by(email=email, purpose=purpose)
        .filter(AuthToken.used_at.is_(None), AuthToken.expires_at >= now)
        .order_by(AuthToken.create_time.desc())
        .all()
    )
    for row in rows:
        if _check_code(code, row.code_hash):
            row.used_at = now
            db.session.commit()
            return True
    return False
