"""认证 API."""
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import db
from app.middleware.auth import get_request_user_id, write_audit
from app.models import User

bp = Blueprint("auth", __name__)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""

    if not name or not account or len(password) < 6:
        return jsonify({"error": "姓名、账号必填，密码至少6位"}), 400

    if User.query.filter_by(account=account).first():
        return jsonify({"error": "账号已存在"}), 400

    user = User(name=name, account=account, password_hash=_hash_password(password), role="user")
    db.session.add(user)
    db.session.commit()
    write_audit("register", "user", user.id)
    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(account=account).first()
    if not user or not _check_password(password, user.password_hash):
        return jsonify({"error": "账号或密码错误"}), 401

    token = create_access_token(identity=str(user.id))
    write_audit("login", "user", user.id)
    return jsonify({"token": token, "user": user.to_dict()})


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify(user.to_dict())


@bp.route("/me", methods=["PUT"])
@jwt_required()
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
@jwt_required()
def change_password():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    if len(new_password) < 6:
        return jsonify({"error": "新密码至少6位"}), 400
    if not _check_password(old_password, user.password_hash):
        return jsonify({"error": "当前密码不正确"}), 400
    user.password_hash = _hash_password(new_password)
    db.session.commit()
    write_audit("change_password", "user", user.id)
    return jsonify({"message": "密码已更新"})
