"""权限装饰器与审计."""
from functools import wraps

import jwt as pyjwt
from flask import current_app, g, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import AuditLog, User


def _jwt_secrets():
    primary = current_app.config.get("JWT_SECRET_KEY")
    legacy = current_app.config.get("JWT_LEGACY_SECRET_KEYS") or []
    secrets = []
    for secret in [primary, *legacy]:
        if secret and secret not in secrets:
            secrets.append(secret)
    return secrets


def _decode_payload(token: str) -> tuple[dict | None, str | None, int | None]:
    """解析 JWT 载荷，兼容多密钥."""
    token = (token or "").strip()
    if not token or token.lower() in {"null", "undefined"}:
        return None, "未登录或令牌无效", 401
    for secret in _jwt_secrets():
        try:
            return pyjwt.decode(token, secret, algorithms=["HS256"]), None, None
        except pyjwt.ExpiredSignatureError:
            return None, "登录已过期，请重新登录", 401
        except Exception:
            continue
    return None, "未登录或令牌无效", 401


def _validate_user_token(payload: dict) -> tuple[User | None, str | None, int | None]:
    sub = payload.get("sub")
    if sub is None:
        return None, "未登录或令牌无效", 401
    try:
        uid = int(sub)
    except (TypeError, ValueError):
        return None, "未登录或令牌无效", 401
    user = User.query.get(uid)
    if not user:
        return None, "用户不存在", 401
    if user.status == "disabled":
        return None, "账号已被禁用，请联系管理员", 403
    token_ver = int(payload.get("ver", 0) or 0)
    if token_ver != int(user.token_version or 0):
        return None, "登录已失效，请重新登录", 401
    return user, None, None


def decode_jwt_token(token: str):
    """解析原始 JWT（WebSocket 等），校验版本与账号状态."""
    payload, err, status = _decode_payload(token)
    if err:
        return None, err, status
    user, err, status = _validate_user_token(payload)
    if err:
        return None, err, status
    return str(user.id), None, None


def resolve_jwt_sub():
    """解析 Authorization Bearer 令牌."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "未登录或令牌无效", 401
    return decode_jwt_token(auth[7:].strip())


def load_current_user() -> User | None:
    """从 g 或 JWT 获取当前用户（需先经过 jwt_required_compat / admin_required）."""
    if getattr(g, "current_user", None) is not None:
        return g.current_user
    if getattr(g, "jwt_sub", None) is not None:
        return User.query.get(int(g.jwt_sub))
    try:
        return User.query.get(int(get_jwt_identity()))
    except Exception:
        return None


def get_request_user_id():
    """优先使用兼容解析结果，否则回退 flask-jwt-extended."""
    if getattr(g, "jwt_sub", None) is not None:
        return int(g.jwt_sub)
    return int(get_jwt_identity())


def bump_token_version(user: User) -> None:
    user.token_version = int(user.token_version or 0) + 1


def _authenticate_request():
    """解析并校验请求令牌，写入 g.jwt_sub / g.current_user."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "未登录或令牌无效", 401
    payload, err, status = _decode_payload(auth[7:].strip())
    if err:
        return None, err, status
    user, err, status = _validate_user_token(payload)
    if err:
        return None, err, status
    g.jwt_sub = str(user.id)
    g.current_user = user
    return user, None, None


def jwt_required_compat(fn):
    """兼容旧密钥 + token_version + 禁用账号的 jwt_required 替代."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        _, err, status = _authenticate_request()
        if err:
            return jsonify({"error": err}), status
        return fn(*args, **kwargs)

    return wrapper


def login_required(fn):
    """替代 jwt_required：统一返回 401，并兼容旧版 JWT 密钥."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        _, err, status = _authenticate_request()
        if err:
            return jsonify({"error": err}), status
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """要求管理员角色且账号有效."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user, err, status = _authenticate_request()
        if err:
            return jsonify({"error": err}), status
        if user.role != "admin":
            return jsonify({"error": "需要管理员权限"}), 403
        return fn(*args, **kwargs)

    return wrapper


def write_audit(action, resource=None, resource_id=None, detail=None):
    """写入审计日志."""
    uid = None
    try:
        user = load_current_user()
        if user:
            uid = user.id
    except Exception:
        try:
            sub, _, _ = resolve_jwt_sub()
            if sub:
                uid = int(sub)
        except Exception:
            try:
                from flask_jwt_extended import verify_jwt_in_request

                verify_jwt_in_request(optional=True)
                ident = get_jwt_identity()
                if ident:
                    uid = int(ident)
            except Exception:
                pass
    log = AuditLog(
        user_id=uid,
        action=action,
        resource=resource,
        resource_id=resource_id,
        detail=detail,
        ip=request.remote_addr if request else None,
    )
    db.session.add(log)
    db.session.commit()
