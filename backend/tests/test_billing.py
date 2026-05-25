"""计费流程单元测试."""
import json

from app import db
from app.models import PaymentOrder, User, UserSubscription
from app.services.billing_service import (
    billing_public_config,
    create_subscription_order,
    mark_order_paid,
    submit_payment_notice,
)


def test_billing_config(client):
    r = client.get("/api/billing/plans")
    assert r.status_code == 200
    assert "plans" in r.json
    assert "config" in r.json
    assert r.json["config"]["order_ttl_minutes"] >= 15


def test_confirm_paid_pending_review(client, app):
    with app.app_context():
        admin = User.query.filter_by(account="admin").first()
        if not admin:
            return
        order = create_subscription_order(admin.id, "pro", "month", "wechat")
        oid = order.id
    login = client.post("/api/auth/login", json={"account": "admin", "password": "admin123"})
    if login.status_code != 200:
        login = client.post("/api/auth/login", json={"account": "admin", "password": "demo123"})
    token = login.json.get("token")
    if not token:
        return
    h = {"Authorization": f"Bearer {token}"}
    r = client.post(f"/api/billing/orders/{oid}/confirm-paid", json={}, headers=h)
    assert r.status_code in (200, 202)
    with app.app_context():
        row = PaymentOrder.query.get(oid)
        if app.config.get("BILLING_DEV_AUTO_PAY") and not app.config.get("IS_PRODUCTION"):
            assert row.status == "paid"
        else:
            assert row.status in ("pending_review", "paid")


def test_mark_order_paid_idempotent(app):
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            return
        order = create_subscription_order(admin.id, "pro", "month", "alipay")
        submit_payment_notice(order)
        mark_order_paid(order, remark="test")
        mark_order_paid(order, remark="test2")
        assert order.status == "paid"
        sub = UserSubscription.query.filter_by(user_id=admin.id).first()
        assert sub and sub.plan_code == "pro"
