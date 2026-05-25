"""SMTP 邮件发送（注册验证码 / 重置密码）."""
from __future__ import annotations

import logging
import re
import smtplib
from email.message import EmailMessage

from flask import current_app

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalize_email(email)))


def send_verification_email(to_email: str, code: str, purpose: str) -> None:
    """发送验证码邮件；开发模式仅写日志."""
    to_email = normalize_email(to_email)
    if purpose == "register":
        subject = "【组队超脑】注册验证码"
        body = f"您的注册验证码为：{code}\n10 分钟内有效，请勿泄露给他人。"
    else:
        subject = "【组队超脑】重置密码验证码"
        body = f"您的重置密码验证码为：{code}\n10 分钟内有效。如非本人操作请忽略本邮件。"

    if current_app.config.get("EMAIL_DEV_MODE"):
        logger.warning("[TEAMMIND_EMAIL_DEV] to=%s purpose=%s code=%s", to_email, purpose, code)
        print(f"[TEAMMIND_EMAIL_DEV] to={to_email} purpose={purpose} code={code}")
        return

    host = current_app.config.get("SMTP_HOST") or ""
    if not host:
        raise RuntimeError("未配置 SMTP_HOST，无法发送邮件。开发环境可设置 TEAMMIND_EMAIL_DEV_MODE=1")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config.get("SMTP_FROM") or current_app.config.get("SMTP_USER") or "noreply@teammind.local"
    msg["To"] = to_email
    msg.set_content(body)

    port = int(current_app.config.get("SMTP_PORT") or 587)
    user = current_app.config.get("SMTP_USER") or ""
    password = current_app.config.get("SMTP_PASS") or ""
    use_tls = current_app.config.get("SMTP_USE_TLS", True)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if use_tls:
            smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)
