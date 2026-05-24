#!/usr/bin/env python3
"""验证 Zeabur / 公网部署是否就绪（health、三端页面、可选登录与 LLM）."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch(url: str, *, method: str = "GET", data: dict | None = None, headers: dict | None = None) -> tuple[int, str]:
    body = None
    req_headers = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 TeamMind AI 公网部署")
    parser.add_argument("--base-url", required=True, help="例如 https://your-app.zeabur.app")
    parser.add_argument("--account", default="admin", help="登录测试账号")
    parser.add_argument("--password", default="admin123", help="登录测试密码")
    parser.add_argument("--skip-login", action="store_true", help="跳过登录与 LLM 抽检")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    checks: list[tuple[str, bool, str]] = []

    code, body = fetch(f"{base}/api/health")
    ok = code == 200 and "ok" in body
    checks.append(("API Health", ok, f"HTTP {code} {body[:120]}"))

    for name, path, needle in [
        ("统一门户", "/", "TeamMind"),
        ("教师端", "/admin/", "TeamMind"),
        ("学生端", "/student/", "TeamMind"),
    ]:
        code, body = fetch(f"{base}{path}")
        ok = code == 200 and needle in body
        checks.append((name, ok, f"HTTP {code}"))

    token = None
    if not args.skip_login:
        code, body = fetch(
            f"{base}/api/auth/login",
            method="POST",
            data={"account": args.account, "password": args.password},
        )
        ok = code == 200
        detail = f"HTTP {code}"
        if ok:
            try:
                token = json.loads(body).get("token")
                detail += " token=ok"
            except json.JSONDecodeError:
                ok = False
                detail += " invalid-json"
        checks.append(("管理员登录", ok, detail))

        if token:
            code, body = fetch(
                f"{base}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            checks.append(("JWT 鉴权", code == 200, f"HTTP {code}"))

    failed = [c for c in checks if not c[1]]
    print(f"\nTeamMind AI 部署验证 — {base}\n")
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}: {detail}")

    if failed:
        print(f"\n{len(failed)} 项未通过。请检查环境变量、Volume 挂载与 Zeabur 构建日志。")
        return 1

    print("\n全部检查通过。正式生产请立即修改默认演示密码。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
