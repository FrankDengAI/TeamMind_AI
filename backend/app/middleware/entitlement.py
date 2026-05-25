"""权益装饰器与 402 响应."""
from __future__ import annotations

from functools import wraps

from flask import jsonify

from app.middleware.auth import get_request_user_id
from app.services.entitlement_service import PaywallError, check_limit, consume_ai_points, get_entitlements


def paywall_response(exc: PaywallError):
    return (
        jsonify(
            {
                "error": str(exc),
                "code": "PAYWALL",
                "feature": exc.feature,
                "upgrade_plan": exc.upgrade_plan,
                "preview": exc.preview,
            }
        ),
        402,
    )


def require_entitlement(limit_key: str):
    """检查套餐限额（不扣点）."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                uid = get_request_user_id()
                check_limit(uid, limit_key)
            except PaywallError as exc:
                return paywall_response(exc)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def consume_ai(feature: str, *, cost: int | None = None, allow_preview: bool = False):
    """扣减 AI 点数."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                uid = get_request_user_id()
                consume_ai_points(uid, feature, cost=cost, allow_preview=allow_preview)
            except PaywallError as exc:
                return paywall_response(exc)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
