"""订单创建、支付确认与套餐激活."""
from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta

from flask import current_app

from app import db
from app.models import PaymentOrder, User
from app.services.entitlement_service import activate_subscription, apply_addon
from app.services.plan_catalog import ADDON_CATALOG, PLAN_CATALOG, get_plan


def _order_no() -> str:
    return f"TM{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4).upper()}"


def _qr_payload(channel: str, order: PaymentOrder) -> dict:
    """生成扫码支付展示数据（静态收款码 + 订单号，适合 MVP）."""
    cfg = current_app.config
    if channel == "wechat":
        url = cfg.get("BILLING_WECHAT_QR_URL", "")
        label = "微信支付"
    else:
        url = cfg.get("BILLING_ALIPAY_QR_URL", "")
        label = "支付宝"
    return {
        "channel": channel,
        "label": label,
        "qr_url": url,
        "order_no": order.order_no,
        "amount": order.amount_cents / 100,
        "amount_cents": order.amount_cents,
        "hint": f"请使用{label}扫码，备注或留言填写订单号：{order.order_no}",
        "manual_confirm": bool(cfg.get("BILLING_MANUAL_CONFIRM", True)),
    }


def create_subscription_order(user_id: int, plan_code: str, period: str, channel: str) -> PaymentOrder:
    plan = get_plan(plan_code)
    if not plan or plan_code == "free":
        raise ValueError("无效套餐")
    if period not in {"month", "year"}:
        raise ValueError("period 须为 month 或 year")
    amount = plan["price_year_cents"] if period == "year" else plan["price_month_cents"]
    if amount <= 0:
        raise ValueError("该套餐无需付费")

    order = PaymentOrder(
        order_no=_order_no(),
        user_id=user_id,
        product_type="subscription",
        plan_code=plan_code,
        period=period,
        amount_cents=amount,
        channel=channel,
        status="pending",
        expire_at=datetime.utcnow() + timedelta(minutes=15),
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
    order = PaymentOrder(
        order_no=_order_no(),
        user_id=user_id,
        product_type="addon",
        addon_code=addon_code,
        amount_cents=amount,
        channel=channel,
        status="pending",
        expire_at=datetime.utcnow() + timedelta(minutes=15),
    )
    order.qr_payload = json.dumps(_qr_payload(channel, order), ensure_ascii=False)
    db.session.add(order)
    db.session.commit()
    return order


def mark_order_paid(order: PaymentOrder, *, remark: str | None = None) -> PaymentOrder:
    if order.status == "paid":
        return order
    if order.expire_at and order.expire_at < datetime.utcnow() and order.status == "pending":
        order.status = "expired"
        db.session.commit()
        raise ValueError("订单已过期")

    order.status = "paid"
    order.paid_at = datetime.utcnow()
    if remark:
        order.remark = remark

    if order.product_type == "subscription" and order.plan_code:
        activate_subscription(order.user_id, order.plan_code, order.period or "month")
    elif order.product_type == "addon" and order.addon_code:
        apply_addon(order.user_id, order.addon_code)

    db.session.commit()
    return order


def expire_stale_orders() -> int:
    now = datetime.utcnow()
    rows = PaymentOrder.query.filter(PaymentOrder.status == "pending", PaymentOrder.expire_at < now).all()
    for row in rows:
        row.status = "expired"
    db.session.commit()
    return len(rows)
