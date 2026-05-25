# TeamMind AI 计费与盈利模块

## 概述

V2 采用 **Freemium + 教师账号订阅**：学生端功能免费；教师（`admin`）按套餐解锁 AI 算力、深度分析与完整导出。支付为 **页面内扫码**（微信/支付宝静态收款码）+ 订单号核销，无需复杂 SaaS 多租户。

## 套餐

| 套餐 | 月付 | 年付 | 要点 |
|------|------|------|------|
| Free | ¥0 | ¥0 | 1 班 30 人、20 AI 点/月、导出预览 |
| Pro | ¥49 | ¥399 | 5 班、500 AI 点、DeepSeek、完整导出 |
| Plus | ¥129 | ¥999 | 多班大班、2000 AI 点、PDF 不限 |

定义见 [`backend/app/services/plan_catalog.py`](../backend/app/services/plan_catalog.py)。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/billing/plans` | 套餐与加购包列表 |
| GET | `/api/billing/me` | 当前教师权益（需登录 admin） |
| POST | `/api/billing/trial` | 领取 7 天 Pro 试用（每账号一次） |
| POST | `/api/billing/orders` | 创建订单并返回收款码信息 |
| GET | `/api/billing/orders/:id` | 轮询订单状态 |
| POST | `/api/billing/orders/:id/confirm-paid` | 用户确认已付款（开发/人工核销） |
| GET | `/api/admin/billing/orders` | 运营订单列表 |
| POST | `/api/admin/billing/orders/:id/fulfill` | 管理员核销 |
| POST | `/api/admin/billing/grant` | 赠送套餐天数 |
| GET | `/api/admin/billing/usage` | AI 用量统计 |

触达付费墙时 API 返回 **HTTP 402**，body 含 `code: "PAYWALL"`。

## AI 点数消耗

| 功能 | 点数 |
|------|------|
| 画像 DeepSeek | 2 |
| 社区发帖 LLM | 1 |
| 班级分组 AI 建议 | 5 |
| 单组 AI 分析（手动刷新） | 2 |
| 活动 AI 复盘（含自动分组时各组 DeepSeek 分析） | 8 |
| 任务分配 AI 说明 | 4 |
| 任务调优 AI 解读 | 3 |
| 团队报告 AI 叙事 | 5 |
| PDF 报告 | 10 |

每月 1 日按 `usage_month` 重置已用点数。

## 环境变量

见 [`.env.example`](../.env.example)：

- `BILLING_WECHAT_QR_URL` / `BILLING_ALIPAY_QR_URL`：收款码图片 URL
- `BILLING_MANUAL_CONFIRM`：是否允许「我已付款」流程
- `BILLING_DEV_AUTO_PAY`：开发环境自动开通（非 production）
- `BILLING_WEBHOOK_SECRET`：回调验签占位

## 前端入口

- **教师端**：顶栏套餐/AI 点数、升级弹窗、`#billing` 订单页
- **门户**：定价区块（`/pricing` 锚点）
- **学生端**：画像页提示「教师开通 Pro 后启用 DeepSeek」（不弹付费墙）

## 数据表

- `subscription_plan` — 套餐定义（启动时从 catalog 同步）
- `user_subscription` — 教师订阅与月度用量
- `payment_order` — 订单
- `ai_usage_log` — 扣点日志
- `feature_override` — 运营赠送点数

## 生产建议

1. 配置企业微信/支付宝商户 Native 扫码，替换静态 URL + webhook 验签。
2. 关闭 `BILLING_DEV_AUTO_PAY`，仅通过核销或回调开通。
3. 监控 `ai_usage_log` 与 DeepSeek 账单，调整 `plan_catalog` 定价。
