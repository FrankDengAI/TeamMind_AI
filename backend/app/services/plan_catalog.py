"""套餐定义与默认限额."""
from __future__ import annotations

import copy
from typing import Any

# 点数消耗（与规划一致）
AI_POINT_COSTS: dict[str, int] = {
    "profile.llm": 2,
    "community.llm": 1,
    "grouping.advice": 5,
    "group.insight": 2,
    "activity.insight": 8,
    "task.assign": 4,
    "task.adjust": 3,
    "report.llm": 5,
    "export.pdf": 10,
    "class.copilot": 3,
}

PLAN_CATALOG: dict[str, dict[str, Any]] = {
    "free": {
        "code": "free",
        "name": "免费版",
        "name_en": "Free",
        "badge": "",
        "badge_en": "",
        "price_month_cents": 0,
        "price_year_cents": 0,
        "highlight": False,
        "limits": {
            "max_classes": 1,
            "max_students_per_class": 30,
            "max_active_activities": 1,
            "ai_points_monthly": 20,
            "deep_grouping_preview_monthly": 1,
            "export_full": False,
            "export_preview_rows": 5,
            "pdf_report_monthly": 0,
            "deep_grouping": False,
            "activity_llm_insight": False,
            "profile_llm_for_class": False,
            "custom_templates_max": 3,
            "command_dashboard_pro": False,
            "class_health_dashboard": True,
            "class_copilot": False,
            "timeline_editable": False,
            "grouping_templates_pro": 0,
            "grouping_scenario_monthly": 0,
            "rubric_sets_max": 0,
            "class_nudge_send": False,
        },
        "features_marketing": [
            "完整跑通 1 次课程组队闭环",
            "规则画像 + 自动分组算法",
            "班级健康度看板（只读）",
            "每月 20 AI 点（预览级）",
        ],
        "features_marketing_en": [
            "Full teaming workflow for one course",
            "Rule-based profiles + auto grouping",
            "Basic command center & task board",
            "20 AI credits/month (preview tier)",
        ],
    },
    "pro": {
        "code": "pro",
        "name": "专业版",
        "name_en": "Pro",
        "badge": "80% 教师选择",
        "badge_en": "Most popular",
        "price_month_cents": 4900,
        "price_year_cents": 39900,
        "highlight": True,
        "limits": {
            "max_classes": 5,
            "max_students_per_class": 80,
            "max_active_activities": 10,
            "ai_points_monthly": 500,
            "deep_grouping_preview_monthly": 9999,
            "export_full": True,
            "export_preview_rows": 0,
            "pdf_report_monthly": 10,
            "deep_grouping": True,
            "activity_llm_insight": True,
            "profile_llm_for_class": True,
            "custom_templates_max": 20,
            "command_dashboard_pro": True,
            "class_health_dashboard": True,
            "class_copilot": True,
            "timeline_editable": True,
            "grouping_templates_pro": 4,
            "grouping_scenario_monthly": 10,
            "rubric_sets_max": 5,
            "class_nudge_send": True,
        },
        "features_marketing": [
            "DeepSeek 画像增强（全班共享）",
            "班级 Copilot + 可编辑学期时间轴",
            "Pro 分组策略模板 + 一键催办",
            "无水印 Excel 导出 + 每月 10 份 PDF",
            "每月 500 AI 点",
        ],
        "features_marketing_en": [
            "DeepSeek profile boost (whole class)",
            "AI grouping advice & activity insights",
            "Watermark-free Excel + 10 PDFs/month",
            "500 AI credits/month",
        ],
    },
    "plus": {
        "code": "plus",
        "name": "旗舰版",
        "name_en": "Plus",
        "badge": "多班导师",
        "badge_en": "Multi-class mentor",
        "price_month_cents": 12900,
        "price_year_cents": 99900,
        "highlight": False,
        "limits": {
            "max_classes": 9999,
            "max_students_per_class": 200,
            "max_active_activities": 9999,
            "ai_points_monthly": 2000,
            "deep_grouping_preview_monthly": 9999,
            "export_full": True,
            "export_preview_rows": 0,
            "pdf_report_monthly": 9999,
            "deep_grouping": True,
            "activity_llm_insight": True,
            "profile_llm_for_class": True,
            "custom_templates_max": 9999,
            "command_dashboard_pro": True,
            "class_health_dashboard": True,
            "class_copilot": True,
            "timeline_editable": True,
            "grouping_templates_pro": 99,
        },
        "features_marketing": [
            "不限班级与活动数量",
            "全部高级分组模板 + 班级 Copilot",
            "每月 2000 AI 点",
            "PDF 报告不限量",
        ],
        "features_marketing_en": [
            "Unlimited classes & activities",
            "Up to 200 students per class",
            "2000 AI credits/month",
            "Unlimited PDF reports",
        ],
    },
}

ADDON_CATALOG: dict[str, dict[str, Any]] = {
    "ai_pack_200": {
        "code": "ai_pack_200",
        "name": "AI 点数包 200",
        "price_cents": 1900,
        "extra_ai_points": 200,
    },
    "ai_pack_1000": {
        "code": "ai_pack_1000",
        "name": "AI 点数包 1000",
        "price_cents": 7900,
        "extra_ai_points": 1000,
    },
    "super_group_report": {
        "code": "super_group_report",
        "name": "超级分组报告（单次）",
        "price_cents": 990,
        "extra_ai_points": 0,
        "grant_feature": "super_group_report_once",
    },
}


def get_plan(code: str) -> dict[str, Any] | None:
    plan = PLAN_CATALOG.get(code)
    return copy.deepcopy(plan) if plan else None


def plan_limits(code: str) -> dict[str, Any]:
    plan = get_plan(code) or get_plan("free")
    return plan["limits"] if plan else PLAN_CATALOG["free"]["limits"]


def all_plans_public() -> list[dict[str, Any]]:
    out = []
    for code in ("free", "pro", "plus"):
        p = get_plan(code)
        if not p:
            continue
        month_cents = p["price_month_cents"]
        year_cents = p["price_year_cents"]
        year_save_pct = 0
        if month_cents > 0 and year_cents > 0:
            year_save_pct = max(0, round((1 - year_cents / (month_cents * 12)) * 100))
        out.append(
            {
                "code": p["code"],
                "name": p["name"],
                "name_en": p["name_en"],
                "badge": p.get("badge"),
                "badge_en": p.get("badge_en") or "",
                "highlight": p.get("highlight", False),
                "price_month": month_cents / 100,
                "price_year": year_cents / 100,
                "price_month_cents": month_cents,
                "price_year_cents": year_cents,
                "year_save_percent": year_save_pct,
                "limits": p["limits"],
                "features": p.get("features_marketing", []),
                "features_en": p.get("features_marketing_en", p.get("features_marketing", [])),
            }
        )
    return out
