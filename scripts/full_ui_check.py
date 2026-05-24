# -*- coding: utf-8 -*-
"""全站 UI 导航与按钮冒烟检测（门户 / 教师端 / 学生端）."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

STUDENT_DEMO_ACCOUNTS = [
    ("zhangsan", "123456"),
    ("student01", "123456"),
    ("student02", "123456"),
]
ACTIVE_STUDENT_ACCOUNT = STUDENT_DEMO_ACCOUNTS[0]


def http_json(method: str, url: str, data=None, token: str | None = None) -> tuple[int, dict | list | str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, raw


class Reporter:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, str]] = []

    def ok(self, name: str) -> None:
        self.items.append(("PASS", name, ""))

    def fail(self, name: str, detail: str) -> None:
        self.items.append(("FAIL", name, detail))

    def exit_code(self) -> int:
        for status, name, detail in self.items:
            line = f"{status}: {name}"
            if detail:
                line += f" -> {detail}"
            print(line)
        passed = sum(1 for s, _, _ in self.items if s == "PASS")
        failed = sum(1 for s, _, _ in self.items if s == "FAIL")
        print(f"\n合计 PASS={passed} FAIL={failed}")
        return 1 if failed else 0


def check_static_pages(base: str, rep: Reporter) -> None:
    pages = [
        ("/", "portal", ["组队超脑", "portal.js", "id=\"app\""]),
        ("/admin/", "admin", ["admin-overview", "app.js"]),
        ("/student/", "student", ["id=\"app\"", "app.js"]),
    ]
    for path, name, markers in pages:
        try:
            req = urllib.request.Request(base + path)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            if resp.status != 200:
                rep.fail(f"static:{name}", f"status={resp.status}")
                continue
            missing = [m for m in markers if m not in html]
            if missing:
                rep.fail(f"static:{name}", f"missing {missing}")
            else:
                rep.ok(f"static:{name}")
        except Exception as exc:  # noqa: BLE001
            rep.fail(f"static:{name}", repr(exc))


def check_api_flow(base: str, rep: Reporter) -> tuple[str | None, str | None]:
    global ACTIVE_STUDENT_ACCOUNT
    admin_token = student_token = None

    code, data = http_json("POST", f"{base}/api/auth/login", {"account": "admin", "password": "admin123"})
    if code == 200 and isinstance(data, dict) and data.get("token"):
        admin_token = data["token"]
        rep.ok("api:admin-login")
    else:
        rep.fail("api:admin-login", f"{code} {data}")
        return None, None

    for path in [
        "/api/admin/overview",
        "/api/admin/users",
        "/api/admin/config",
        "/api/admin/templates",
        "/api/admin/team-activities",
        "/api/admin/classes",
        "/api/admin/dashboard",
    ]:
        code, data = http_json("GET", f"{base}{path}", token=admin_token)
        if code == 200:
            rep.ok(f"api:admin-get:{path.split('/')[-1]}")
        else:
            rep.fail(f"api:admin-get:{path.split('/')[-1]}", f"{code} {data}")

    last_student_error = None
    for account, password in STUDENT_DEMO_ACCOUNTS:
        code, data = http_json("POST", f"{base}/api/auth/login", {"account": account, "password": password})
        if code == 200 and isinstance(data, dict) and data.get("token"):
            student_token = data["token"]
            ACTIVE_STUDENT_ACCOUNT = (account, password)
            rep.ok(f"api:student-login:{account}")
            break
        last_student_error = f"{account}: {code} {data}"
    if not student_token:
        account = f"teammind_smoke_{int(time.time())}"
        code, data = http_json(
            "POST",
            f"{base}/api/auth/register",
            {"name": "冒烟测试学生", "account": account, "password": "123456"},
        )
        if code in {200, 201} and isinstance(data, dict) and data.get("token"):
            student_token = data["token"]
            ACTIVE_STUDENT_ACCOUNT = (account, "123456")
            rep.ok(f"api:student-register:{account}")
        else:
            rep.fail("api:student-login", last_student_error or f"register failed: {code} {data}")
            return admin_token, None

    for path in ["/api/auth/me", "/api/profile/tags/catalog", "/api/team-activities/active", "/api/community/feed"]:
        code, data = http_json("GET", f"{base}{path}", token=student_token)
        if code == 200:
            rep.ok(f"api:student-get:{path.split('/')[-1]}")
        else:
            rep.fail(f"api:student-get:{path.split('/')[-1]}", f"{code} {data}")

    code, bad = http_json("GET", f"{base}/api/admin/overview", token="bad.token")
    if code == 401:
        rep.ok("api:invalid-token-401")
    else:
        rep.fail("api:invalid-token-401", f"expected 401 got {code} {bad}")

    return admin_token, student_token


def run_playwright(base: str, rep: Reporter) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        rep.fail("playwright", "未安装 playwright，跳过浏览器检测")
        return

    def goto(page, url: str) -> None:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # --- Portal ---
            page = browser.new_page(viewport={"width": 1440, "height": 960})
            try:
                goto(page, base + "/")
                page.wait_for_selector('[data-action="login"]', timeout=45000)
                page.click('[data-action="toggle-settings"]', timeout=5000)
                page.wait_for_selector(".settings-panel:not([hidden])", timeout=5000)
                for lang in ["en", "zh-Hant", "zh-CN"]:
                    page.click(f'[data-lang="{lang}"]', timeout=5000)
                page.click('[data-action="login"]', timeout=5000)
                page.wait_for_selector(".role-modal:not([hidden])", timeout=5000)
                assert page.locator('a[href="/admin/"]').count() >= 1
                assert page.locator('a[href="/student/"]').count() >= 1
                page.click('[data-action="close"]', timeout=5000)
                page.click('a[href="#workflow"]', timeout=5000)
                page.click('a[href="#product"]', timeout=5000)
                rep.ok("ui:portal-buttons")
            except Exception as exc:  # noqa: BLE001
                rep.fail("ui:portal-buttons", repr(exc))

            # --- Admin ---
            admin = browser.new_page(viewport={"width": 1440, "height": 960})
            try:
                goto(admin, base + "/admin/")
                admin.wait_for_selector(".el-input__inner", timeout=15000)
                inputs = admin.locator(".el-input__inner")
                inputs.nth(0).fill("admin")
                inputs.nth(1).fill("admin123")
                admin.locator("button.el-button--primary").first.click(timeout=8000)
                admin.wait_for_selector(".layout", timeout=20000)
                nav_keys = ["classes", "workbench", "users", "community", "export", "settings"]
                for key in nav_keys:
                    admin.locator(f'a.nav-item[href="#{key}"], a.nav-item').filter(has_text="").first
                    admin.evaluate(f"window.location.hash = '#{key}'")
                    admin.wait_for_timeout(400)
                admin.locator('.nav-item').nth(0).click(timeout=5000)
                admin.locator('.nav-item').nth(1).click(timeout=5000)
                admin.locator('.nav-item').nth(2).click(timeout=5000)
                admin.locator('.nav-item').nth(3).click(timeout=5000)
                admin.locator('.nav-item').nth(4).click(timeout=5000)
                admin.locator('.nav-item').nth(5).click(timeout=5000)
                admin.locator('.user-chip').click(timeout=5000)
                admin.locator('text=个人主页').first.click(timeout=5000)
                admin.wait_for_timeout(300)
                admin.go_back(timeout=5000)
                admin.go_forward(timeout=5000)
                admin.locator('button').filter(has_text="刷新").first.click(timeout=5000)
                admin.wait_for_timeout(500)
                admin.locator('.aside-switch a').first.click(timeout=5000)
                admin.wait_for_timeout(800)
                assert "/student/" in admin.url
                rep.ok("ui:admin-nav-account-history")
            except Exception as exc:  # noqa: BLE001
                rep.fail("ui:admin-nav-account-history", repr(exc))

            # --- Student ---
            student = browser.new_page(viewport={"width": 1440, "height": 960})
            try:
                goto(student, base + "/student/")
                student.wait_for_selector(".el-input__inner", timeout=15000)
                inputs = student.locator(".el-input__inner")
                inputs.nth(0).fill(ACTIVE_STUDENT_ACCOUNT[0])
                inputs.nth(1).fill(ACTIVE_STUDENT_ACCOUNT[1])
                student.locator("button.el-button--primary").first.click(timeout=8000)
                student.wait_for_selector(".layout", timeout=20000)
                for idx in range(min(6, student.locator(".nav-item").count())):
                    student.locator(".nav-item").nth(idx).click(timeout=5000)
                    student.wait_for_timeout(350)
                student.locator(".user-chip, .avatar").first.click(timeout=5000)
                student.locator('text=个人主页').first.click(timeout=5000)
                student.wait_for_timeout(300)
                student.go_back(timeout=5000)
                student.go_forward(timeout=5000)
                href = student.locator(".aside-switch a, .role-switch-card").first.get_attribute("href")
                if not href:
                    rep.fail("ui:student-switch-admin-link", "missing admin link")
                else:
                    student.locator(".aside-switch a, .role-switch-card").first.click(timeout=5000)
                    student.wait_for_timeout(800)
                    assert "/admin/" in student.url
                    rep.ok("ui:student-nav-account-history")
            except Exception as exc:  # noqa: BLE001
                rep.fail("ui:student-nav-account-history", repr(exc))
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="全站 UI/API 检测")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--skip-playwright", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    rep = Reporter()

    print("=== 静态页与资源 ===")
    check_static_pages(base, rep)

    print("\n=== API 登录与核心接口 ===")
    check_api_flow(base, rep)

    if not args.skip_playwright:
        print("\n=== Playwright 按钮/导航 ===")
        run_playwright(base, rep)

    return rep.exit_code()


if __name__ == "__main__":
    sys.exit(main())
