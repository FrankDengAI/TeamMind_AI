"""订阅、订单与 AI 用量模型."""
from __future__ import annotations

import json
from datetime import datetime

from app import db


class SubscriptionPlan(db.Model):
    """套餐定义（启动时从 plan_catalog 同步）."""

    __tablename__ = "subscription_plan"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    limits_json = db.Column(db.Text, nullable=False)
    price_month_cents = db.Column(db.Integer, default=0)
    price_year_cents = db.Column(db.Integer, default=0)
    meta_json = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def limits(self) -> dict:
        try:
            return json.loads(self.limits_json or "{}")
        except (TypeError, json.JSONDecodeError):
            return {}

    def to_dict(self):
        meta = {}
        if self.meta_json:
            try:
                meta = json.loads(self.meta_json)
            except (TypeError, json.JSONDecodeError):
                pass
        return {
            "code": self.code,
            "name": self.name,
            "limits": self.limits(),
            "price_month_cents": self.price_month_cents,
            "price_year_cents": self.price_year_cents,
            "meta": meta,
        }


class UserSubscription(db.Model):
    """教师账号订阅状态."""

    __tablename__ = "user_subscription"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False, index=True)
    plan_code = db.Column(db.String(32), default="free", nullable=False, index=True)
    status = db.Column(db.String(32), default="active", index=True)  # active | expired | trial
    period = db.Column(db.String(16), default="month")  # month | year | trial
    expire_at = db.Column(db.DateTime)
    ai_points_used = db.Column(db.Integer, default=0)
    ai_points_extra = db.Column(db.Integer, default=0)
    pdf_reports_used = db.Column(db.Integer, default=0)
    deep_preview_used = db.Column(db.Integer, default=0)
    usage_month = db.Column(db.String(7), index=True)  # YYYY-MM
    trial_used = db.Column(db.Boolean, default=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "plan_code": self.plan_code,
            "status": self.status,
            "period": self.period,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "ai_points_used": self.ai_points_used or 0,
            "ai_points_extra": self.ai_points_extra or 0,
            "pdf_reports_used": self.pdf_reports_used or 0,
            "deep_preview_used": self.deep_preview_used or 0,
            "usage_month": self.usage_month,
            "trial_used": bool(self.trial_used),
        }


class PaymentOrder(db.Model):
    """支付订单."""

    __tablename__ = "payment_order"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    product_type = db.Column(db.String(32), default="subscription")  # subscription | addon
    plan_code = db.Column(db.String(32))
    addon_code = db.Column(db.String(32))
    period = db.Column(db.String(16))  # month | year
    amount_cents = db.Column(db.Integer, nullable=False)
    channel = db.Column(db.String(16))  # wechat | alipay
    status = db.Column(db.String(32), default="pending", index=True)  # pending | paid | expired | cancelled
    qr_payload = db.Column(db.Text)
    paid_at = db.Column(db.DateTime)
    expire_at = db.Column(db.DateTime)
    remark = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, *, include_qr: bool = False):
        d = {
            "id": self.id,
            "order_no": self.order_no,
            "user_id": self.user_id,
            "product_type": self.product_type,
            "plan_code": self.plan_code,
            "addon_code": self.addon_code,
            "period": self.period,
            "amount_cents": self.amount_cents,
            "amount": self.amount_cents / 100,
            "channel": self.channel,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
        if include_qr and self.qr_payload:
            try:
                d["qr"] = json.loads(self.qr_payload)
            except (TypeError, json.JSONDecodeError):
                d["qr"] = {"raw": self.qr_payload}
        return d


class AiUsageLog(db.Model):
    """AI 点数消耗日志."""

    __tablename__ = "ai_usage_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    feature = db.Column(db.String(64), index=True)
    points_cost = db.Column(db.Integer, default=0)
    tokens_est = db.Column(db.Integer, default=0)
    ref_type = db.Column(db.String(32))
    ref_id = db.Column(db.Integer)
    detail = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "feature": self.feature,
            "points_cost": self.points_cost,
            "tokens_est": self.tokens_est,
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class FeatureOverride(db.Model):
    """运营赠送：额外点数、延期等."""

    __tablename__ = "feature_override"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    extra_ai_points = db.Column(db.Integer, default=0)
    extend_days = db.Column(db.Integer, default=0)
    plan_code = db.Column(db.String(32))
    note = db.Column(db.Text)
    expire_at = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "extra_ai_points": self.extra_ai_points,
            "extend_days": self.extend_days,
            "plan_code": self.plan_code,
            "note": self.note,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
        }
