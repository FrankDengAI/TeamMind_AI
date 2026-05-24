"""浏览器级冒烟自检：门户、教师端、学生端登录与导航.

运行前先启动服务：
    python main.py --no-browser
然后执行：
    python scripts/ui_smoke_test.py --base-url http://127.0.0.1:5000
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="TeamMind UI smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--admin-account", default="admin")
    parser.add_argument("--admin-password", default="admin123")
    parser.add_argument("--student-account", default="zhangsan")
    parser.add_argument("--student-password", default="123456")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("缺少 Playwright，请先执行: pip install playwright && playwright install chromium")
        return 2

    base = args.base_url.rstrip("/")
    results: list[tuple[str, str, str]] = []

    def ok(name: str) -> None:
        results.append(("PASS", name, ""))

    def fail(name: str, exc: Exception) -> None:
        results.append(("FAIL", name, repr(exc)))

    def goto(page, url: str) -> None:
        page.goto(url, wait_until="commit", timeout=20000)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            try:
                goto(page, base + "/")
                page.locator('[data-action="login"]').first.wait_for(state="visible", timeout=10000)
                page.locator('[data-action="toggle-settings"]').click(timeout=5000)
                page.locator(".settings-panel").wait_for(state="visible", timeout=5000)
                page.locator('[data-lang="en"]').click(timeout=5000)
                assert page.evaluate("localStorage.getItem('teammind_portal_lang')") == "en"
                page.locator('[data-action="zh-Hant"], [data-lang="zh-Hant"]').click(timeout=5000)
                assert page.evaluate("localStorage.getItem('teammind_portal_lang')") == "zh-Hant"
                page.locator('[data-action="login"]').first.click(timeout=5000)
                page.locator(".role-modal:not([hidden])").wait_for(state="visible", timeout=5000)
                assert page.locator('a[href="/admin/"]').count() == 1
                assert page.locator('a[href="/student/"]').count() == 1
                ok("portal")
            except Exception as exc:  # noqa: BLE001
                fail("portal", exc)

            admin = browser.new_page(viewport={"width": 1440, "height": 1000})
            try:
                goto(admin, base + "/admin/")
                admin.locator(".el-input__inner").nth(0).wait_for(state="visible", timeout=15000)
                admin.locator(".el-input__inner").nth(0).fill(args.admin_account)
                admin.locator(".el-input__inner").nth(1).fill(args.admin_password)
                admin.locator("button.el-button--primary").first.click(timeout=5000)
                admin.locator(".layout").wait_for(state="visible", timeout=15000)
                assert admin.locator(".nav-list a").count() >= 5
                ok("admin")
            except Exception as exc:  # noqa: BLE001
                fail("admin", exc)

            student = browser.new_page(viewport={"width": 1440, "height": 1000})
            try:
                goto(student, base + "/student/")
                student.locator(".el-input__inner").nth(0).wait_for(state="visible", timeout=15000)
                student.locator(".el-input__inner").nth(0).fill(args.student_account)
                student.locator(".el-input__inner").nth(1).fill(args.student_password)
                student.locator("button.el-button--primary").first.click(timeout=5000)
                student.locator(".layout").wait_for(state="visible", timeout=15000)
                assert student.locator(".nav-list a").count() >= 5
                ok("student")
            except Exception as exc:  # noqa: BLE001
                fail("student", exc)
        finally:
            browser.close()

    for status, name, detail in results:
        print(f"{status}: {name}" + (f" -> {detail}" if detail else ""))
    return 1 if any(status == "FAIL" for status, _, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
