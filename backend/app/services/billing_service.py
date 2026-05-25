"""订单创建、支付确认与套餐激活."""
from __future__ import annotations

import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import update

from app import db
from app.models import PaymentOrder, User
from app.services.entitlement_service import activate_subscription, apply_addon, get_entitlements
from app.services.plan_catalog import ADDON_CATALOG, PLAN_CATALOG, get_plan

PAYABLE_STATUSES = ("pending", "pending_review")
ORDER_TTL_MINUTES = 30


def _order_no() -> str:
    return f"TM{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4).upper()}"


def _order_ttl_minutes() -> int:
    return int(current_app.config.get("BILLING_ORDER_TTL_MINUTES", ORDER_TTL_MINUTES))


def billing_public_config() -> dict:
    """前端支付流程配置（无需登录）."""
    cfg = current_app.config
    is_prod = bool(cfg.get("IS_PRODUCTION"))
    dev_auto = bool(cfg.get("BILLING_DEV_AUTO_PAY")) and not is_prod
    wechat = (cfg.get("BILLING_WECHAT_QR_URL") or "").strip()
    alipay = (cfg.get("BILLING_ALIPAY_QR_URL") or "").strip()
    return {
        "dev_auto_pay": dev_auto,
        "manual_confirm": not dev_auto,
        "is_production": is_prod,
        "order_ttl_minutes": _order_ttl_minutes(),
        "qr_configured": {"wechat": bool(wechat), "alipay": bool(alipay)},
        "payment_ready": dev_auto or bool(wechat or alipay),
    }


def _qr_payload(channel: str, order: PaymentOrder) -> dict:
    """生成扫码支付展示数据（静态收款码 + 订单号，适合 MVP）."""
    cfg = current_app.config
    dev_auto = billing_public_config()["dev_auto_pay"]
    if channel == "wechat":
        url = (cfg.get("BILLING_WECHAT_QR_URL") or "").strip()
        label = "微信支付"
    else:
        url = (cfg.get("BILLING_ALIPAY_QR_URL") or "").strip()
        label = "支付宝"
    hint = f"请使用{label}扫码支付"
    if url:
        hint += f"，备注或留言填写订单号：{order.order_no}"
    elif dev_auto:
        hint += "；开发环境可点击「我已付款」自动开通"
    else:
        hint += "；支付后点击「我已付款」，管理员将在订单页核销开通"
    return {
        "channel": channel,
        "label": label,
        "qr_url": url,
        "order_no": order.order_no,
        "amount": order.amount_cents / 100,
        "amount_cents": order.amount_cents,
        "hint": hint,
        "dev_auto_pay": dev_auto,
    }


def refresh_order_lifecycle(order: PaymentOrder) -> PaymentOrder:
    """读取订单时同步过期状态."""
    if order.status in PAYABLE_STATUSES and order.expire_at and order.expire_at < datetime.utcnow():
        order.status = "expired"
        db.session.commit()
    return order


def _cancel_user_payable_orders(user_id: int) -> int:
    rows = PaymentOrder.query.filter(
        PaymentOrder.user_id == user_id,
        PaymentOrder.status.in_(PAYABLE_STATUSES),
    ).all()
    for row in rows:
        row.status = "cancelled"
        row.remark = (row.remark or "") + " | superseded"
    if rows:
        db.session.commit()
    return len(rows)


def create_subscription_order(user_id: int, plan_code: str, period: str, channel: str) -> PaymentOrder:
    plan = get_plan(plan_code)
    if not plan or plan_code == "free":
        raise ValueError("无效套餐")
    if period not in {"month", "year"}:
        raise ValueError("period 须为 month 或 year")
    amount = plan["price_year_cents"] if period == "year" else plan["price_month_cents"]
    if amount <= 0:
        raise ValueError("该套餐无需付费")

    ent = get_entitlements(user_id)
    if ent["plan_code"] == plan_code and ent.get("expire_at"):
        try:
            exp = datetime.fromisoformat(str(ent["expire_at"]).replace("Z", "")[:19])
        except ValueError:
            exp = None
        if exp and exp > datetime.utcnow():
            raise ValueError("当前套餐仍在有效期内，无需重复购买")

    _cancel_user_payable_orders(user_id)
    ttl = _order_ttl_minutes()
    order = PaymentOrder(
        order_no=_order_no(),
        user_id=user_id,
        product_type="subscription",
        plan_code=plan_code,
        period=period,
        amount_cents=amount,
        channel=channel,
        status="pending",
        expire_at=datetime.utcnow() + timedelta(minutes=ttl),
    )
    order.qr_payload = json.dumps(_qr_payload(channel, order), ensure_ascii=False)
    db.session.add(order)
    db.session.commit()
    return order


def create_addon_order(user_id: int, addon_code: str, channel: str) -> PaymentOrder:
    addon = ADDON_CATALOG.get(addon_code)
    if not addon:
        raise ValueError("无效加购包")
    amount = addon["price_cents"]
    if amount <= 0:
        raise ValueError("该加购无需付费")

    _cancel_user_payable_orders(user_id)
    ttl = _order_ttl_minutes()
    order = PaymentOrder(
        order_no=_order_no(),
        user_id=user_id,
        product_type="addon",
        addon_code=addon_code,
        amount_cents=amount,
        channel=channel,
        status="pending",
        expire_at=datetime.utcnow() + timedelta(minutes=ttl),
    )
    order.qr_payload = json.dumps(_qr_payload(channel, order), ensure_ascii=False)
    db.session.add(order)
    db.session.commit()
    return order


def submit_payment_notice(order: PaymentOrder, *, remark: str | None = None) -> PaymentOrder:
    """用户声明已付款，进入待核销队列."""
    refresh_order_lifecycle(order)
    if order.status == "pending_review":
        return order
    if order.status != "pending":
        raise ValueError("订单状态不可提交核销")
    order.status = "pending_review"
    order.remark = remark or "user_submitted_payment"
    db.session.commit()
    return order


def cancel_order(order: PaymentOrder) -> PaymentOrder:
    refresh_order_lifecycle(order)
    if order.status not in PAYABLE_STATUSES:
        raise ValueError("只能取消待支付或待核销订单")
    order.status = "cancelled"
    order.remark = (order.remark or "") + " | user_cancelled"
    db.session.commit()
    return order


def mark_order_paid(order: PaymentOrder, *, remark: str | None = None) -> PaymentOrder:
    refresh_order_lifecycle(order)
    if order.status == "paid":
        return order
    if order.status == "expired":
        raise ValueError("订单已过期")
    if order.status not in PAYABLE_STATUSES:
        raise ValueError("订单状态不可支付")

    values = {"status": "paid", "paid_at": datetime.utcnow()}
    if remark:
        values["remark"] = remark
    updated = db.session.execute(
        update(PaymentOrder)
        .where(PaymentOrder.id == order.id, PaymentOrder.status.in_(PAYABLE_STATUSES))
        .values(**values)
    ).rowcount
    db.session.refresh(order)
    if updated == 0:
        if order.status == "paid":
            return order
        if order.status == "expired":
            raise ValueError("订单已过期")
        raise ValueError("订单状态不可支付")

    if order.product_type == "subscription" and order.plan_code:
        activate_subscription(order.user_id, order.plan_code, order.period or "month")
    elif order.product_type == "addon" and order.addon_code:
        apply_addon(order.user_id, order.addon_code)

    db.session.commit()
    return order


def verify_webhook_sign(provided: str, secret: str) -> bool:
    if not secret or not provided:
        return False
    return hmac.compare_digest(str(provided), str(secret))


def list_user_orders(user_id: int, *, limit: int = 20) -> list[PaymentOrder]:
    rows = (
        PaymentOrder.query.filter_by(user_id=user_id)
        .order_by(PaymentOrder.create_time.desc())
        .limit(limit)
        .all()
    )
    for row in rows:
        refresh_order_lifecycle(row)
    return rows


def pending_review_count() -> int:
    return PaymentOrder.query.filter_by(status="pending_review").count()


def expire_stale_orders() -> int:
    now = datetime.utcnow()
    rows = PaymentOrder.query.filter(
        PaymentOrder.status.in_(PAYABLE_STATUSES),
        PaymentOrder.expire_at < now,
    ).all()
    for row in rows:
        row.status = "expired"
    if rows:
        db.session.commit()
    return len(rows)
