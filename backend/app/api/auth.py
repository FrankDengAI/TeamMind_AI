"""认证 API."""
from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import or_

from app import db
from app.middleware.auth import bump_token_version, get_request_user_id, jwt_required_compat, write_audit
from app.models import User
from app.services.auth_verification import (
    account_from_email,
    issue_email_code,
    normalize_email,
    validate_account_name,
    validate_password_strength,
    verify_email_code,
)
from app.services.email_service import is_valid_email

bp = Blueprint("auth", __name__)

_LOGIN_FAILURES: dict[str, list[datetime]] = {}
_LOCK_THRESHOLD = 5
_LOCK_MINUTES = 15


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _lock_key(identifier: str) -> str:
    return normalize_email(identifier) if "@" in identifier else identifier.strip().lower()


def _is_login_locked(identifier: str) -> bool:
    key = _lock_key(identifier)
    now = datetime.utcnow()
    attempts = [t for t in _LOGIN_FAILURES.get(key, []) if now - t < timedelta(minutes=_LOCK_MINUTES)]
    _LOGIN_FAILURES[key] = attempts
    return len(attempts) >= _LOCK_THRESHOLD


def _record_login_failure(identifier: str) -> None:
    _LOGIN_FAILURES.setdefault(_lock_key(identifier), []).append(datetime.utcnow())


def _clear_login_failures(identifier: str) -> None:
    _LOGIN_FAILURES.pop(_lock_key(identifier), None)


def _email_auth_enabled() -> bool:
    return not current_app.config.get("DISABLE_EMAIL_AUTH", True)


def _find_user_by_login(identifier: str) -> User | None:
    ident = (identifier or "").strip()
    if not ident:
        return None
    if not _email_auth_enabled():
        return User.query.filter_by(account=ident).first()
    if "@" in ident:
        return User.query.filter_by(email=normalize_email(ident)).first()
    return User.query.filter(
        or_(User.account == ident, User.email == normalize_email(ident))
    ).first()


def _user_response(user: User) -> dict:
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"ver": int(user.token_version or 0)},
    )
    return {"token": token, "user": user.to_dict()}


@bp.route("/email/send-code", methods=["POST"])
def send_email_code():
    if not _email_auth_enabled():
        return jsonify({"error": "当前仅支持账号密码注册，无需邮箱验证码"}), 403
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email") or "")
    purpose = (data.get("purpose") or "register").strip()
    if not is_valid_email(email):
        return jsonify({"error": "邮箱格式不正确"}), 400
    try:
        issue_email_code(email, purpose)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    write_audit("send_email_code", "auth", None, email)
    return jsonify({"message": "验证码已发送"})


@bp.route("/register/email", methods=["POST"])
def register_email():
    if not _email_auth_enabled():
        return jsonify({"error": "请使用账号密码注册"}), 403
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email") or "")
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""

    if not is_valid_email(email):
        return jsonify({"error": "邮箱格式不正确"}), 400
    if not name:
        return jsonify({"error": "姓名不能为空"}), 400
    pw_err = validate_password_strength(password)
    if pw_err:
        return jsonify({"error": pw_err}), 400
    if not verify_email_code(email, "register", code):
        return jsonify({"error": "验证码无效或已过期"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "该邮箱已注册"}), 400

    user = User(
        name=name,
        account=account_from_email(email),
        email=email,
        email_verified_at=datetime.utcnow(),
        password_hash=_hash_password(password),
        role="user",
        is_demo=False,
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    write_audit("register_email", "user", user.id)
    return jsonify(_user_response(user)), 201


@bp.route("/register", methods=["POST"])
def register():
    if not current_app.config.get("ALLOW_LEGACY_REGISTER", True):
        return jsonify({"error": "注册已关闭，请联系管理员"}), 403
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""

    if not name:
        return jsonify({"error": "姓名不能为空"}), 400
    acc_err = validate_account_name(account)
    if acc_err:
        return jsonify({"error": acc_err}), 400
    pw_err = validate_password_strength(password)
    if pw_err:
        return jsonify({"error": pw_err}), 400

    if User.query.filter_by(account=account).first():
        return jsonify({"error": "账号已存在"}), 400

    user = User(
        name=name,
        account=account,
        password_hash=_hash_password(password),
        role="user",
        is_demo=False,
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    write_audit("register", "user", user.id)
    return jsonify(_user_response(user)), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""

    if _is_login_locked(account):
        return jsonify({"error": "登录失败次数过多，请 15 分钟后再试"}), 429

    user = _find_user_by_login(account)
    if not user:
        _record_login_failure(account)
        write_audit("login_failed", "user", None, account)
        return jsonify({"error": "账号或密码错误"}), 401
    if user.status == "disabled":
        _record_login_failure(account)
        write_audit("login_failed", "user", user.id, account)
        return jsonify({"error": "账号已被禁用，请联系管理员"}), 403
    if not _check_password(password, user.password_hash):
        _record_login_failure(account)
        write_audit("login_failed", "user", user.id, account)
        return jsonify({"error": "账号或密码错误"}), 401

    _clear_login_failures(account)
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    write_audit("login", "user", user.id)
    return jsonify(_user_response(user))


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    if not _email_auth_enabled():
        return jsonify({"error": "请登录后在个人主页修改密码，或联系管理员重置"}), 403
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email") or "")
    if not is_valid_email(email):
        return jsonify({"error": "邮箱格式不正确"}), 400
    user = User.query.filter_by(email=email).first()
    if user and user.status != "disabled":
        try:
            issue_email_code(email, "reset_password")
        except (ValueError, RuntimeError):
            pass
    write_audit("forgot_password", "user", user.id if user else None)
    return jsonify({"message": "若邮箱已注册，将收到验证码"})


@bp.route("/reset-password", methods=["POST"])
def reset_password():
    if not _email_auth_enabled():
        return jsonify({"error": "请登录后在个人主页修改密码，或联系管理员重置"}), 403
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email") or "")
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or data.get("password") or ""

    if not is_valid_email(email):
        return jsonify({"error": "邮箱格式不正确"}), 400
    pw_err = validate_password_strength(new_password)
    if pw_err:
        return jsonify({"error": pw_err}), 400
    if not verify_email_code(email, "reset_password", code):
        return jsonify({"error": "验证码无效或已过期"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    if user.status == "disabled":
        return jsonify({"error": "账号已被禁用"}), 403

    user.password_hash = _hash_password(new_password)
    bump_token_version(user)
    db.session.commit()
    write_audit("reset_password", "user", user.id)
    return jsonify({"message": "密码已重置，请重新登录"})


@bp.route("/me", methods=["GET"])
@jwt_required_compat
def me():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify(user.to_dict())


@bp.route("/me", methods=["PUT"])
@jwt_required_compat
def update_me():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    avatar_url = (data.get("avatar_url") or "").strip()
    bio = (data.get("bio") or "").strip()
    headline = (data.get("headline") or "").strip()
    portfolio_url = (data.get("portfolio_url") or "").strip()
    github_url = (data.get("github_url") or "").strip()
    research_interest = (data.get("research_interest") or "").strip()
    availability = (data.get("availability") or "").strip()
    display_theme = (data.get("display_theme") or "").strip()
    if not name:
        return jsonify({"error": "姓名不能为空"}), 400
    if len(name) > 64:
        return jsonify({"error": "姓名不能超过64个字符"}), 400
    if len(avatar_url) > 512:
        return jsonify({"error": "头像地址过长"}), 400
    if len(bio) > 240:
        return jsonify({"error": "个人介绍不能超过240个字符"}), 400
    if len(headline) > 120 or len(research_interest) > 240 or len(availability) > 120:
        return jsonify({"error": "展示信息过长"}), 400
    if len(portfolio_url) > 512 or len(github_url) > 512:
        return jsonify({"error": "链接地址过长"}), 400
    user.name = name
    user.avatar_url = avatar_url or None
    user.bio = bio or None
    user.headline = headline or None
    user.portfolio_url = portfolio_url or None
    user.github_url = github_url or None
    user.research_interest = research_interest or None
    user.availability = availability or None
    user.display_theme = display_theme or None
    db.session.commit()
    write_audit("update_me", "user", user.id)
    return jsonify(user.to_dict())


@bp.route("/change-password", methods=["POST"])
@jwt_required_compat
def change_password():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    pw_err = validate_password_strength(new_password)
    if pw_err:
        return jsonify({"error": pw_err}), 400
    if not _check_password(old_password, user.password_hash):
        return jsonify({"error": "当前密码不正确"}), 400
    user.password_hash = _hash_password(new_password)
    bump_token_version(user)
    db.session.commit()
    write_audit("change_password", "user", user.id)
    return jsonify({"message": "密码已更新"})
