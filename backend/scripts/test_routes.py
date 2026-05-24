"""路由自检：管理后台界面与用户静态资源."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app

ROOT = Path(__file__).resolve().parent.parent.parent
WEB = ROOT / "web_embedded"
WEB_ADMIN = ROOT / "web_embedded_admin"


def test_admin_with_ui():
    app = create_app(serve_static=True, static_ui="admin")
    client = app.test_client()
    ok = True
    r_health = client.get("/api/health")
    r_root = client.get("/")
    print(f"[{'OK' if r_health.status_code == 200 else 'FAIL'}] admin /api/health -> {r_health.status_code}")
    print(f"[{'OK' if r_root.status_code == 200 else 'FAIL'}] admin / -> {r_root.status_code} (应为200)")
    body = r_root.get_data(as_text=True)
    has_marker = "TeamMind Admin" in body or "admin-overview" in body
    print(f"[{'OK' if has_marker else 'FAIL'}] admin 页面含管理标识")
    if r_health.status_code != 200 or r_root.status_code != 200 or not has_marker:
        ok = False
    return ok


def test_embedded_files_exist():
    files = ["index.html", "assets/app.js", "assets/config.js", "assets/style.css"]
    ok = True
    for label, root in [("web_embedded", WEB), ("web_embedded_admin", WEB_ADMIN)]:
        for f in files:
            exists = (root / f).is_file()
            print(f"[{'OK' if exists else 'FAIL'}] {label}/{f}")
            if not exists:
                ok = False
    return ok


def main():
    print("=== TeamMind 路由自检 ===\n")
    a = test_admin_with_ui()
    print()
    b = test_embedded_files_exist()
    print()
    return 0 if (a and b) else 1


if __name__ == "__main__":
    sys.exit(main())
