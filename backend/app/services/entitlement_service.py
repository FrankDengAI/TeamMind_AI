"""权益解析、限额检查与 AI 点数扣减."""
from __future__ import annotations

from datetime import datetime, timedelta

from app import db
from app.models import AiUsageLog, ClassMembership, Classroom, FeatureOverride, TeamActivity, User, UserSubscription
from app.services.plan_catalog import AI_POINT_COSTS, get_plan, plan_limits

ACTIVE_ACTIVITY_STATUSES = {
    "collecting",
    "grouping",
    "preview",
    "confirming",
    "published",
    "locked",
    "tasking",
    "adjusting",
}


class PaywallError(Exception):
    """触发付费墙."""

    def __init__(self, message: str, *, feature: str, upgrade_plan: str = "pro", preview: dict | None = None):
        super().__init__(message)
        self.feature = feature
        self.upgrade_plan = upgrade_plan
        self.preview = preview or {}


def _current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _effective_plan_code(sub: UserSubscription | None) -> str:
    if not sub:
        return "free"
    if sub.status == "trial" and sub.expire_at and sub.expire_at > datetime.utcnow():
        return sub.plan_code or "pro"
    if sub.plan_code and sub.plan_code != "free":
        if sub.expire_at and sub.expire_at < datetime.utcnow():
            return "free"
        if sub.status in {"active", "trial"}:
            return sub.plan_code
    return "free"


def get_or_create_subscription(user_id: int) -> UserSubscription:
    sub = UserSubscription.query.filter_by(user_id=user_id).first()
    month = _current_month()
    if not sub:
        sub = UserSubscription(user_id=user_id, plan_code="free", status="active", usage_month=month)
        db.session.add(sub)
        db.session.commit()
        return sub
    if sub.usage_month != month:
        sub.usage_month = month
        sub.ai_points_used = 0
        sub.pdf_reports_used = 0
        sub.deep_preview_used = 0
        db.session.commit()
    return sub


def _override_extra_points(user_id: int) -> int:
    now = datetime.utcnow()
    rows = FeatureOverride.query.filter_by(user_id=user_id).all()
    total = 0
    for row in rows:
        if row.expire_at and row.expire_at < now:
            continue
        total += row.extra_ai_points or 0
    return total


def get_entitlements(user_id: int) -> dict:
    """返回教师账号完整权益快照（供 /billing/me）."""
    user = User.query.get(user_id)
    if not user:
        raise ValueError("用户不存在")
    sub = get_or_create_subscription(user_id)
    plan_code = _effective_plan_code(sub)
    limits = plan_limits(plan_code)
    monthly_quota = limits.get("ai_points_monthly", 20)
    extra = (sub.ai_points_extra or 0) + _override_extra_points(user_id)
    used = sub.ai_points_used or 0
    ai_remaining = max(0, monthly_quota + extra - used)

    class_count = Classroom.query.filter(Classroom.teacher_id == user_id, Classroom.status == "active").count()
    active_activities = (
        TeamActivity.query.join(Classroom, TeamActivity.class_id == Classroom.id)
        .filter(Classroom.teacher_id == user_id, TeamActivity.status.in_(ACTIVE_ACTIVITY_STATUSES))
        .count()
    )

    plan = get_plan(plan_code) or get_plan("free")
    return {
        "user_id": user_id,
        "role": user.role,
        "plan_code": plan_code,
        "plan_name": plan["name"] if plan else "免费版",
        "plan_name_en": (plan.get("name_en") or plan["name"]) if plan else "Free",
        "status": sub.status,
        "period": sub.period,
        "expire_at": sub.expire_at.isoformat() if sub.expire_at else None,
        "trial_used": bool(sub.trial_used),
        "limits": limits,
        "usage": {
            "ai_points_used": used,
            "ai_points_monthly": monthly_quota,
            "ai_points_extra": extra,
            "ai_points_remaining": ai_remaining,
            "pdf_reports_used": sub.pdf_reports_used or 0,
            "pdf_reports_monthly": limits.get("pdf_report_monthly", 0),
            "deep_preview_used": sub.deep_preview_used or 0,
            "class_count": class_count,
            "active_activities": active_activities,
        },
        "flags": {
            "export_full": bool(limits.get("export_full")),
            "deep_grouping": bool(limits.get("deep_grouping")),
            "activity_llm_insight": bool(limits.get("activity_llm_insight")),
            "profile_llm_for_class": bool(limits.get("profile_llm_for_class")),
            "command_dashboard_pro": bool(limits.get("command_dashboard_pro")),
        },
    }


def resolve_teacher_id_for_student(student_id: int, class_id: int | None = None) -> int | None:
    """学生画像 LLM 跟随班级教师权益."""
    if class_id:
        cls = Classroom.query.get(class_id)
        if cls and cls.teacher_id:
            return cls.teacher_id
    membership = (
        ClassMembership.query.filter_by(user_id=student_id, status="active")
        .order_by(ClassMembership.update_time.desc())
        .first()
    )
    if membership:
        cls = Classroom.query.get(membership.class_id)
        if cls and cls.teacher_id:
            return cls.teacher_id
    return None


def check_limit(user_id: int, key: str, *, current: int | None = None, increment: int = 0) -> None:
    ent = get_entitlements(user_id)
    limits = ent["limits"]
    usage = ent["usage"]

    if key == "max_classes":
        cap = limits.get("max_classes", 1)
        count = current if current is not None else usage["class_count"]
        if count + increment > cap:
            raise PaywallError(
                f"免费版最多 {cap} 个班级，升级 Pro 可创建最多 5 个班级",
                feature="max_classes",
                preview={"current": count, "max": cap},
            )
    elif key == "max_students_per_class":
        cap = limits.get("max_students_per_class", 30)
        count = current or 0
        if count + increment > cap:
            raise PaywallError(
                f"当前套餐每班最多 {cap} 人，升级后可扩容",
                feature="max_students_per_class",
                preview={"current": count, "max": cap},
            )
    elif key == "max_active_activities":
        cap = limits.get("max_active_activities", 1)
        count = current if current is not None else usage["active_activities"]
        if count + increment > cap:
            raise PaywallError(
                f"当前套餐最多 {cap} 个进行中的组队活动，升级后可同时管理更多活动",
                feature="max_active_activities",
                preview={"current": count, "max": cap},
            )
    elif key == "export_full":
        if not limits.get("export_full"):
            raise PaywallError("完整导出需升级专业版", feature="export.full")
    elif key == "pdf_report":
        cap = limits.get("pdf_report_monthly", 0)
        used = usage["pdf_reports_used"]
        if cap <= 0:
            raise PaywallError("PDF 团队报告需升级专业版", feature="export.pdf")
        if used >= cap:
            raise PaywallError(f"本月 PDF 报告已达上限（{cap} 份）", feature="export.pdf")
    elif key == "deep_grouping":
        if not limits.get("deep_grouping"):
            raise PaywallError("DeepSeek 深度分组分析需升级专业版", feature="grouping.deep")
    elif key == "activity_llm_insight":
        if not limits.get("activity_llm_insight"):
            raise PaywallError("活动 AI 复盘需升级专业版", feature="activity.insight")
    elif key == "profile_llm_for_class":
        if not limits.get("profile_llm_for_class"):
            raise PaywallError("班级 AI 画像增强需教师开通专业版", feature="profile.llm")


def consume_ai_points(
    user_id: int,
    feature: str,
    *,
    cost: int | None = None,
    ref_type: str | None = None,
    ref_id: int | None = None,
    allow_preview: bool = False,
) -> dict:
    """扣减 AI 点数；allow_preview 时免费档可消耗预览额度."""
    cost = cost if cost is not None else AI_POINT_COSTS.get(feature, 1)
    sub = get_or_create_subscription(user_id)
    ent = get_entitlements(user_id)
    remaining = ent["usage"]["ai_points_remaining"]

    if remaining < cost:
        if allow_preview and ent["plan_code"] == "free":
            preview_cap = ent["limits"].get("deep_grouping_preview_monthly", 1)
            if feature in {"grouping.advice", "grouping.deep"} and (sub.deep_preview_used or 0) < preview_cap:
                sub.deep_preview_used = (sub.deep_preview_used or 0) + 1
                db.session.commit()
                return {"preview": True, "points_charged": 0}
        raise PaywallError(
            f"AI 点数不足（需要 {cost} 点，剩余 {remaining} 点）",
            feature=feature,
            preview={"required": cost, "remaining": remaining},
        )

    sub.ai_points_used = (sub.ai_points_used or 0) + cost
    log = AiUsageLog(
        user_id=user_id,
        feature=feature,
        points_cost=cost,
        ref_type=ref_type,
        ref_id=ref_id,
    )
    db.session.add(log)
    db.session.commit()
    return {"preview": False, "points_charged": cost}


def blur_ai_text(text: str, *, visible_chars: int = 80) -> str:
    raw = (text or "").strip()
    if len(raw) <= visible_chars:
        return raw + " …（升级 Pro 查看完整 AI 分析）"
    return raw[:visible_chars] + "…（升级 Pro 解锁完整 DeepSeek 分析）"


def mask_ai_analysis(analysis: dict | None, *, entitled: bool) -> dict:
    if not analysis or entitled:
        return analysis or {}
    out = dict(analysis)
    for key in ("summary", "rationale", "teacher_actions", "risks", "comparison"):
        val = out.get(key)
        if isinstance(val, str):
            out[key] = blur_ai_text(val)
        elif isinstance(val, list):
            out[key] = [blur_ai_text(str(x), visible_chars=40) for x in val[:2]]
    out["locked"] = True
    out["upgrade_hint"] = "升级专业版解锁完整 DeepSeek 分析"
    return out


def activate_subscription(user_id: int, plan_code: str, period: str, *, days: int | None = None) -> UserSubscription:
    sub = get_or_create_subscription(user_id)
    sub.plan_code = plan_code
    sub.status = "active"
    sub.period = period
    if days:
        base = sub.expire_at if sub.expire_at and sub.expire_at > datetime.utcnow() else datetime.utcnow()
        sub.expire_at = base + timedelta(days=days)
    elif period == "year":
        sub.expire_at = datetime.utcnow() + timedelta(days=365)
    elif period == "month":
        sub.expire_at = datetime.utcnow() + timedelta(days=30)
    elif period == "trial":
        sub.status = "trial"
        sub.expire_at = datetime.utcnow() + timedelta(days=7)
    db.session.commit()
    return sub


def start_pro_trial(user_id: int) -> UserSubscription:
    sub = get_or_create_subscription(user_id)
    if sub.trial_used:
        raise PaywallError("您已使用过 Pro 试用", feature="trial")
    sub.trial_used = True
    sub.plan_code = "pro"
    sub.status = "trial"
    sub.period = "trial"
    sub.expire_at = datetime.utcnow() + timedelta(days=7)
    sub.ai_points_used = 0
    db.session.commit()
    return sub


def apply_addon(user_id: int, addon_code: str) -> None:
    from app.services.plan_catalog import ADDON_CATALOG

    addon = ADDON_CATALOG.get(addon_code)
    if not addon:
        return
    sub = get_or_create_subscription(user_id)
    extra = addon.get("extra_ai_points") or 0
    if extra:
        sub.ai_points_extra = (sub.ai_points_extra or 0) + extra
    db.session.commit()
