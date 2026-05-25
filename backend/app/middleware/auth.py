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


def decode_jwt_token(token: str):
    """解析原始 JWT 字符串，兼容品牌升级前后的密钥（供 WebSocket 等场景使用）."""
    token = (token or "").strip()
    if not token or token.lower() in {"null", "undefined"}:
        return None, "未登录或令牌无效", 401
    for secret in _jwt_secrets():
        try:
            payload = pyjwt.decode(token, secret, algorithms=["HS256"])
            sub = payload.get("sub")
            if sub is not None:
                return str(sub), None, None
        except pyjwt.ExpiredSignatureError:
            return None, "登录已过期，请重新登录", 401
        except Exception:
            continue
    return None, "未登录或令牌无效", 401


def resolve_jwt_sub():
    """解析 Authorization Bearer 令牌，兼容品牌升级前后的 JWT 密钥."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "未登录或令牌无效", 401
    token = auth[7:].strip()
    return decode_jwt_token(token)


def get_request_user_id():
    """优先使用兼容解析结果，否则回退 flask-jwt-extended."""
    if getattr(g, "jwt_sub", None) is not None:
        return int(g.jwt_sub)
    return int(get_jwt_identity())


def login_required(fn):
    """替代 jwt_required：统一返回 401，并兼容旧版 JWT 密钥."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        sub, err, status = resolve_jwt_sub()
        if err:
            return jsonify({"error": err}), status
        g.jwt_sub = sub
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """要求管理员角色."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        sub, err, status = resolve_jwt_sub()
        if err:
            return jsonify({"error": err}), status
        uid = int(sub)
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "需要管理员权限"}), 403
        g.jwt_sub = sub
        return fn(*args, **kwargs)

    return wrapper


def write_audit(action, resource=None, resource_id=None, detail=None):
    """写入审计日志."""
    uid = None
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
