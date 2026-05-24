"""前端静态资源路径解析."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VUE_DIST = ROOT / "frontend" / "dist"
WEB_EMBEDDED = ROOT / "web_embedded"
WEB_EMBEDDED_ADMIN = ROOT / "web_embedded_admin"
WEB_PORTAL = ROOT / "web_portal"


def resolve_frontend_dir() -> Path:
    """用户端内置前端."""
    source = os.environ.get("TEAMMIND_STUDENT_UI", "auto").strip().lower()
    if source == "embedded":
        return WEB_EMBEDDED
    if source == "dist":
        return VUE_DIST if (VUE_DIST / "index.html").is_file() else WEB_EMBEDDED
    if (VUE_DIST / "index.html").is_file():
        return VUE_DIST
    return WEB_EMBEDDED


def resolve_admin_dir() -> Path:
    """管理后台可视化界面."""
    return WEB_EMBEDDED_ADMIN


def resolve_portal_dir() -> Path:
    """公网统一门户."""
    return WEB_PORTAL if (WEB_PORTAL / "index.html").is_file() else WEB_EMBEDDED_ADMIN


def frontend_source_name(static_ui: str | None = None) -> str:
    if static_ui == "admin":
        return "管理后台界面 (web_embedded_admin)"
    if static_ui == "portal":
        return "统一公网门户 (web_portal)"
    d = resolve_frontend_dir()
    if d == VUE_DIST:
        return "Vue 构建版 (frontend/dist)"
    return "用户界面 (web_embedded)"
