"""计费与支付 API."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.middleware.auth import get_request_user_id, login_required
from app.middleware.entitlement import paywall_response
from app.models import PaymentOrder, User
from app.services.billing_service import (
    billing_public_config,
    cancel_order,
    create_addon_order,
    create_subscription_order,
    list_user_orders,
    mark_order_paid,
    pending_review_count,
    refresh_order_lifecycle,
    submit_payment_notice,
    verify_webhook_sign,
)
from app.services.entitlement_service import PaywallError, get_entitlements, start_pro_trial
from app.services.plan_catalog import ADDON_CATALOG, AI_POINT_COSTS, all_plans_public

bp = Blueprint("billing", __name__)

_STATUS_LABELS = {
    "pending": "待支付",
    "pending_review": "待核销",
    "paid": "已支付",
    "expired": "已过期",
    "cancelled": "已取消",
}


def _order_payload(order: PaymentOrder, *, include_payment: bool = True) -> dict:
    d = order.to_dict(include_qr=True)
    d["status_label"] = _STATUS_LABELS.get(order.status, order.status)
    if include_payment:
        cfg = billing_public_config()
        wechat = (current_app.config.get("BILLING_WECHAT_QR_URL") or "").strip()
        alipay = (current_app.config.get("BILLING_ALIPAY_QR_URL") or "").strip()
        d["payment"] = {
            "wechat_qr_url": wechat,
            "alipay_qr_url": alipay,
            "selected_channel": order.channel,
            "config": cfg,
        }
    return d


def _require_teacher(uid: int):
    user = User.query.get(uid)
    if not user:
        return None, jsonify({"error": "用户不存在"}), 404
    if user.role != "admin":
        return None, jsonify({"error": "仅教师账号可使用计费功能"}), 403
    return user, None, None


@bp.route("/config", methods=["GET"])
def billing_config():
    """支付流程配置（是否开发自动付、收款码是否就绪等）."""
    return jsonify(billing_public_config())


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
    return jsonify(
        {
            "plans": all_plans_public(),
            "addons": addons,
            "ai_point_costs": AI_POINT_COSTS,
            "config": billing_public_config(),
        }
    )


@bp.route("/me", methods=["GET"])
@login_required
def billing_me():
    uid = get_request_user_id()
    _, err, status = _require_teacher(uid)
    if err:
        return err, status
    ent = get_entitlements(uid)
    payable = (
        PaymentOrder.query.filter(
            PaymentOrder.user_id == uid,
            PaymentOrder.status.in_(("pending", "pending_review")),
        )
        .order_by(PaymentOrder.create_time.desc())
        .first()
    )
    if payable:
        refresh_order_lifecycle(payable)
    ent["billing"] = {
        "config": billing_public_config(),
        "active_order": _order_payload(payable, include_payment=True) if payable and payable.status in ("pending", "pending_review") else None,
        "pending_review_count": pending_review_count(),
    }
    return jsonify(ent)


@bp.route("/orders", methods=["GET"])
@login_required
def list_my_orders():
    uid = get_request_user_id()
    _, err, status = _require_teacher(uid)
    if err:
        return err, status
    rows = list_user_orders(uid)
    return jsonify([_order_payload(o, include_payment=False) for o in rows])


@bp.route("/trial", methods=["POST"])
@login_required
def start_trial():
    uid = get_request_user_id()
    _, err, status = _require_teacher(uid)
    if err:
        return err, status
    try:
        start_pro_trial(uid)
        return jsonify({"message": "已开通 7 天 Pro 试用", "entitlements": get_entitlements(uid)})
    except PaywallError as exc:
        return paywall_response(exc)


@bp.route("/orders", methods=["POST"])
@login_required
def create_order():
    uid = get_request_user_id()
    _, err, status = _require_teacher(uid)
    if err:
        return err, status

    data = request.get_json(silent=True) or {}
    channel = (data.get("channel") or "wechat").strip().lower()
    if channel not in {"wechat", "alipay"}:
        return jsonify({"error": "channel 须为 wechat 或 alipay"}), 400

    cfg = billing_public_config()
    if not cfg["dev_auto_pay"] and not cfg["qr_configured"].get(channel):
        return jsonify({"error": f"未配置{channel}收款码，请联系管理员或设置环境变量"}), 503

    try:
        if data.get("addon_code"):
            order = create_addon_order(uid, data["addon_code"], channel)
        else:
            plan_code = (data.get("plan_code") or "pro").strip()
            period = (data.get("period") or "month").strip()
            order = create_subscription_order(uid, plan_code, period, channel)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_order_payload(order)), 201


@bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    uid = get_request_user_id()
    order = PaymentOrder.query.get_or_404(order_id)
    if order.user_id != uid:
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "无权查看该订单"}), 403
    refresh_order_lifecycle(order)
    return jsonify(_order_payload(order))


@bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_user_order(order_id):
    uid = get_request_user_id()
    order = PaymentOrder.query.get_or_404(order_id)
    if order.user_id != uid:
        return jsonify({"error": "无权操作该订单"}), 403
    try:
        cancel_order(order)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "订单已取消", "order": _order_payload(order, include_payment=False)})


@bp.route("/orders/<int:order_id>/confirm-paid", methods=["POST"])
@login_required
def confirm_paid(order_id):
    """开发环境自动开通；生产环境提交待核销."""
    uid = get_request_user_id()
    order = PaymentOrder.query.get_or_404(order_id)
    if order.user_id != uid:
        return jsonify({"error": "无权操作该订单"}), 403
    refresh_order_lifecycle(order)
    if order.status == "paid":
        return jsonify({"message": "订单已支付", "order": _order_payload(order), "entitlements": get_entitlements(uid)})
    if order.status not in ("pending", "pending_review"):
        return jsonify({"error": "订单不可确认", "order": _order_payload(order)}), 400

    dev_auto = billing_public_config()["dev_auto_pay"]
    data = request.get_json(silent=True) or {}
    if dev_auto:
        try:
            mark_order_paid(order, remark=data.get("remark") or "dev_auto_pay")
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(
            {
                "message": "支付已确认，权益已开通（开发环境）",
                "order": _order_payload(order),
                "entitlements": get_entitlements(uid),
            }
        )

    try:
        submit_payment_notice(order, remark=data.get("remark") or "user_submitted_payment")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "message": "已提交核销申请，管理员确认后将自动开通权益",
            "order": _order_payload(order),
            "entitlements": get_entitlements(uid),
        }
    ), 202


@bp.route("/webhook/wechat", methods=["POST"])
def webhook_wechat():
    return _webhook_stub("wechat")


@bp.route("/webhook/alipay", methods=["POST"])
def webhook_alipay():
    return _webhook_stub("alipay")


def _webhook_stub(channel: str):
    """支付回调：验签通过后开通权益."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    order_no = data.get("order_no") or data.get("out_trade_no")
    if not order_no:
        return jsonify({"error": "missing order_no"}), 400
    order = PaymentOrder.query.filter_by(order_no=str(order_no)).first()
    if not order:
        return jsonify({"error": "order not found"}), 404
    secret = (current_app.config.get("BILLING_WEBHOOK_SECRET") or "").strip()
    if current_app.config.get("IS_PRODUCTION") and not secret:
        return jsonify({"error": "webhook not configured"}), 503
    sign = data.get("sign") or request.headers.get("X-TeamMind-Sign", "")
    if not verify_webhook_sign(sign, secret):
        return jsonify({"error": "invalid sign"}), 403
    try:
        mark_order_paid(order, remark=f"webhook:{channel}")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "order_no": order.order_no})
