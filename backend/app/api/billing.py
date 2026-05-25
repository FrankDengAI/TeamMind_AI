"""计费与支付 API."""
from __future__ import annotations

import json

from flask import Blueprint, current_app, jsonify, request

from app import db
from app.middleware.auth import admin_required, get_request_user_id, login_required
from app.middleware.entitlement import paywall_response
from app.models import PaymentOrder, User
from app.services.billing_service import create_addon_order, create_subscription_order, mark_order_paid
from app.services.entitlement_service import PaywallError, get_entitlements, start_pro_trial
from app.services.plan_catalog import ADDON_CATALOG, all_plans_public

bp = Blueprint("billing", __name__)


@bp.route("/plans", methods=["GET"])
def list_plans():
    addons = [
        {
            "code": a["code"],
            "name": a["name"],
            "price": a["price_cents"] / 100,
            "price_cents": a["price_cents"],
            "extra_ai_points": a.get("extra_ai_points", 0),
        }
        for a in ADDON_CATALOG.values()
    ]
    return jsonify({"plans": all_plans_public(), "addons": addons})


@bp.route("/me", methods=["GET"])
@login_required
def billing_me():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    if user.role != "admin":
        return jsonify({"error": "仅教师账号可查看订阅权益"}), 403
    return jsonify(get_entitlements(uid))


@bp.route("/trial", methods=["POST"])
@login_required
def start_trial():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user or user.role != "admin":
        return jsonify({"error": "仅教师账号可领取试用"}), 403
    try:
        start_pro_trial(uid)
        return jsonify({"message": "已开通 7 天 Pro 试用", "entitlements": get_entitlements(uid)})
    except PaywallError as exc:
        return paywall_response(exc)


@bp.route("/orders", methods=["POST"])
@login_required
def create_order():
    uid = get_request_user_id()
    user = User.query.get(uid)
    if not user or user.role != "admin":
        return jsonify({"error": "仅教师账号可下单"}), 403

    data = request.get_json(silent=True) or {}
    channel = (data.get("channel") or "wechat").strip().lower()
    if channel not in {"wechat", "alipay"}:
        return jsonify({"error": "channel 须为 wechat 或 alipay"}), 400

    try:
        if data.get("addon_code"):
            order = create_addon_order(uid, data["addon_code"], channel)
        else:
            plan_code = (data.get("plan_code") or "pro").strip()
            period = (data.get("period") or "month").strip()
            order = create_subscription_order(uid, plan_code, period, channel)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    payload = order.to_dict(include_qr=True)
    wechat = current_app.config.get("BILLING_WECHAT_QR_URL", "")
    alipay = current_app.config.get("BILLING_ALIPAY_QR_URL", "")
    payload["payment"] = {
        "wechat_qr_url": wechat,
        "alipay_qr_url": alipay,
        "selected_channel": channel,
    }
    return jsonify(payload), 201


@bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    uid = get_request_user_id()
    order = PaymentOrder.query.get_or_404(order_id)
    if order.user_id != uid:
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "无权查看该订单"}), 403
    return jsonify(order.to_dict(include_qr=True))


@bp.route("/orders/<int:order_id>/confirm-paid", methods=["POST"])
@login_required
def confirm_paid_dev(order_id):
    """用户提交已付款（人工核销模式）或开发环境模拟支付."""
    uid = get_request_user_id()
    order = PaymentOrder.query.get_or_404(order_id)
    if order.user_id != uid:
        return jsonify({"error": "无权操作该订单"}), 403
    if order.status != "pending":
        return jsonify(order.to_dict()), 200

    manual = current_app.config.get("BILLING_MANUAL_CONFIRM", True)
    dev_auto = current_app.config.get("BILLING_DEV_AUTO_PAY", False) and not current_app.config.get("IS_PRODUCTION")
    data = request.get_json(silent=True) or {}
    if not manual and not dev_auto:
        return jsonify({"error": "请等待支付平台回调确认"}), 400
    if dev_auto or data.get("confirm") is True:
        try:
            mark_order_paid(order, remark=data.get("remark") or "user_confirm")
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(
            {
                "message": "支付已确认，权益已开通",
                "order": order.to_dict(),
                "entitlements": get_entitlements(uid),
            }
        )
    return jsonify({"message": "已记录，等待管理员核销", "order": order.to_dict()}), 202


@bp.route("/webhook/wechat", methods=["POST"])
def webhook_wechat():
    return _webhook_stub("wechat")


@bp.route("/webhook/alipay", methods=["POST"])
def webhook_alipay():
    return _webhook_stub("alipay")


def _webhook_stub(channel: str):
    """支付回调占位：生产环境接入微信/支付宝验签后调用 mark_order_paid."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    order_no = data.get("order_no") or data.get("out_trade_no")
    if not order_no:
        return jsonify({"error": "missing order_no"}), 400
    order = PaymentOrder.query.filter_by(order_no=str(order_no)).first()
    if not order:
        return jsonify({"error": "order not found"}), 404
    secret = current_app.config.get("BILLING_WEBHOOK_SECRET", "")
    if secret and data.get("sign") != secret:
        return jsonify({"error": "invalid sign"}), 403
    mark_order_paid(order, remark=f"webhook:{channel}")
    return jsonify({"ok": True})
