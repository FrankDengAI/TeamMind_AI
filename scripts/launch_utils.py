"""TeamMind AI 启动公共工具（main / main_admin / main_user 共用）."""
from __future__ import annotations

import functools
import http.server
import importlib.util
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"


def _load_local_env() -> None:
    """启动前加载项目根目录 .env，确保邮件开发模式等对子进程生效。"""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value


_load_local_env()
FRONTEND_DIR = ROOT / "frontend"
WEB_EMBEDDED = ROOT / "web_embedded"
WEB_EMBEDDED_ADMIN = ROOT / "web_embedded_admin"
WEB_PORTAL = ROOT / "web_portal"
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "teammind.db"
LEGACY_DB_FILE = DATA_DIR / "teamforge.db"
INIT_SCRIPT = ROOT / "database" / "init_db.py"

DEFAULT_BACKEND_PORT = int(os.environ.get("PORT", "5000"))
DEFAULT_USER_PORT = 8080
DEFAULT_BACKEND_URL = f"http://127.0.0.1:{DEFAULT_BACKEND_PORT}"


def log(msg: str, prefix: str = "TeamMind") -> None:
    print(f"[{prefix}] {msg}", flush=True)


def check_python_deps() -> bool:
    missing = []
    for mod, pkg in [
        ("flask", "Flask"),
        ("flask_cors", "Flask-CORS"),
        ("flask_jwt_extended", "Flask-JWT-Extended"),
        ("flask_sqlalchemy", "Flask-SQLAlchemy"),
        ("bcrypt", "bcrypt"),
    ]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        log("缺少依赖: " + ", ".join(missing))
        log("请执行: pip install -r backend/requirements.txt --index-url https://pypi.org/simple/")
        return False
    return True


def ensure_data_dirs() -> None:
    if not DB_FILE.exists() and LEGACY_DB_FILE.exists():
        LEGACY_DB_FILE.rename(DB_FILE)
    (DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "private_uploads" / "resumes").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)


def init_database(force: bool = False) -> None:
    if DB_FILE.exists() and not force:
        log(f"数据库已存在: {DB_FILE}")
        return
    log("正在初始化数据库...")
    spec = importlib.util.spec_from_file_location("init_db", INIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 database/init_db.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
    log("数据库初始化完成")


def http_get(url: str, timeout: float = 2) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception:
        return 0, b""


def api_health_ok(base_url: str = DEFAULT_BACKEND_URL) -> bool:
    url = base_url.rstrip("/") + "/api/health"
    code, _ = http_get(url)
    return code == 200


def frontend_ok(port: int) -> bool:
    code, body = http_get(f"http://127.0.0.1:{port}/")
    return code == 200 and (
        b"TeamMind" in body or b'id="app"' in body or b"/assets/app.js" in body
    )


def admin_ui_ok(port: int) -> bool:
    code, body = http_get(f"http://127.0.0.1:{port}/")
    return code == 200 and (b"TeamMind Portal" in body or b"TeamMind Admin" in body or "组队超脑".encode("utf-8") in body or b"admin-overview" in body)


def pids_on_port(port: int) -> list[int]:
    pids: list[int] = []
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            pattern = re.compile(rf":{port}\s+.*LISTENING\s+(\d+)", re.I)
            for line in out.stdout.splitlines():
                m = pattern.search(line.replace("\t", " "))
                if m:
                    pids.append(int(m.group(1)))
        else:
            out = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
            for line in out.stdout.split():
                if line.strip().isdigit():
                    pids.append(int(line.strip()))
    except Exception:
        pass
    return list(dict.fromkeys(pids))


def free_port(port: int) -> bool:
    my_pid = os.getpid()
    killed = False
    for pid in pids_on_port(port):
        if pid == my_pid:
            continue
        log(f"端口 {port} 被 PID={pid} 占用，正在结束...")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            else:
                subprocess.run(["kill", "-9", str(pid)], capture_output=True)
            killed = True
        except Exception as e:
            log(f"无法结束 PID={pid}: {e}")
    if killed:
        time.sleep(1.5)
    return not pids_on_port(port)


def prepare_backend_port(port: int = DEFAULT_BACKEND_PORT, no_kill: bool = True) -> bool:
    """准备后台 API 端口（仅 /api/*，根路径应为 404）."""
    base = f"http://127.0.0.1:{port}"
    if not pids_on_port(port):
        return True

    api_ok = api_health_ok(base)
    if api_ok and admin_ui_ok(port):
        if no_kill:
            log(f"后台 API + 管理界面已在端口 {port} 运行")
            return True
        log(f"后台 API + 管理界面已在端口 {port} 运行，正在重启以加载最新后台与管理端...")
        return free_port(port)

    if api_ok:
        log(f"端口 {port} 上服务不含管理可视化界面，将重启为完整后台模式...")

    if no_kill:
        log(f"端口 {port} 被占用，无法启动后台")
        return False

    log(f"端口 {port} 被占用，尝试释放...")
    if not free_port(port):
        log(f"无法释放端口 {port}")
        return False
    return True


def prepare_user_port(port: int = DEFAULT_USER_PORT, no_kill: bool = True) -> bool:
    if not pids_on_port(port):
        return True
    if frontend_ok(port):
        log(f"用户界面已在端口 {port} 运行")
        return True
    if no_kill:
        return False
    return free_port(port)


def wait_backend_ready(base_url: str = DEFAULT_BACKEND_URL, timeout: float = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if api_health_ok(base_url):
            return True
        time.sleep(0.5)
    return False


def wait_admin_ready(port: int = DEFAULT_BACKEND_PORT, timeout: float = 30) -> bool:
    """等待后台 API + 管理可视化界面就绪."""
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if api_health_ok(base) and admin_ui_ok(port):
            return True
        time.sleep(0.5)
    return False


def run_flask_server(port: int, serve_static: bool = False, static_ui: str | None = None, host: str = "127.0.0.1") -> None:
    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)
    from app import create_app, socketio

    app = create_app(serve_static=serve_static, static_ui=static_ui)
    if socketio is not None:
        socketio.run(app, host=host, port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    else:
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)


def start_flask_thread(
    port: int, serve_static: bool = False, static_ui: str | None = None, host: str = "127.0.0.1"
) -> threading.Thread:
    t = threading.Thread(
        target=run_flask_server,
        args=(port, serve_static),
        kwargs={"static_ui": static_ui, "host": host},
        daemon=True,
    )
    t.start()
    return t


def read_app_version(app_js: Path) -> str | None:
    try:
        text = app_js.read_text(encoding="utf-8")
        m = re.search(r"const APP_VERSION = '([^']+)'", text)
        return m.group(1) if m else None
    except OSError:
        return None


def log_static_bundle(label: str, root: Path) -> None:
    ver = read_app_version(root / "assets" / "app.js")
    ver_txt = f" v{ver}" if ver else ""
    log(f"{label} 静态目录: {root}{ver_txt}", label)


def restart_user_frontend(user_port: int, *, no_kill: bool = True) -> bool:
    """释放学员端端口并确保可启动，避免旧进程继续托管过期静态文件."""
    if not pids_on_port(user_port):
        return True
    if no_kill:
        log(f"端口 {user_port} 被占用（--no-kill-port），无法加载最新学员端前端", "User")
        return False
    log(f"端口 {user_port} 已有旧学员端进程，正在重启以加载最新前端...", "User")
    return free_port(user_port)


def write_user_api_config(backend_url: str = DEFAULT_BACKEND_URL) -> Path:
    """写入前端 API 地址配置（跨端口）."""
    api_base = backend_url.rstrip("/") + "/api"
    config_path = WEB_EMBEDDED / "assets" / "config.js"
    config_path.write_text(
        "// 由 TeamMind 启动器自动生成\n"
        f"window.TEAMMIND_API_BASE = location.port === '{DEFAULT_USER_PORT}' ? '{api_base}' : '/api';\n"
        f"window.TEAMMIND_ADMIN_URL = location.port === '{DEFAULT_USER_PORT}' ? '{backend_url.rstrip('/')}/admin/' : '/admin/';\n",
        encoding="utf-8",
    )
    return config_path


class TeamMindHandler(http.server.SimpleHTTPRequestHandler):
    """托管 web_embedded 静态资源."""

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(WEB_EMBEDDED), **kwargs)

    def log_message(self, fmt, *args):
        log(f"{self.address_string()} - {fmt % args}", "User")


def run_user_http_server(port: int = DEFAULT_USER_PORT, host: str = "127.0.0.1") -> None:
    handler = functools.partial(TeamMindHandler, directory=str(WEB_EMBEDDED))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((host, port), handler) as httpd:
        httpd.serve_forever()


def start_user_http_thread(port: int = DEFAULT_USER_PORT, host: str = "127.0.0.1") -> threading.Thread:
    t = threading.Thread(target=run_user_http_server, args=(port, host), daemon=True)
    t.start()
    return t


def launch_all(
    *,
    backend_port: int = DEFAULT_BACKEND_PORT,
    user_port: int = DEFAULT_USER_PORT,
    init_db: bool = False,
    no_kill_port: bool = False,
    kill_port: bool = False,
    no_browser: bool = False,
    admin_only: bool = False,
    user_only: bool = False,
    start_legacy_user: bool = False,
    backend_wait: float = 30,
    host: str = "127.0.0.1",
) -> int:
    """统一启动：默认只启动 5000 统一门户；8080 仅由 main_user.py 兼容启动."""
    no_kill_port = no_kill_port or not kill_port
    backend_url = f"http://127.0.0.1:{backend_port}"
    admin_url = f"{backend_url}/"
    user_url = f"http://127.0.0.1:{user_port}/"

    if admin_only and user_only:
        log("不能同时指定 admin_only 与 user_only")
        return 1

    if not user_only:
        if not (WEB_PORTAL / "index.html").is_file():
            log(f"缺少统一门户文件: {WEB_PORTAL}", "Portal")
            return 1
        if not (WEB_EMBEDDED_ADMIN / "index.html").is_file():
            log(f"缺少管理界面文件: {WEB_EMBEDDED_ADMIN}", "Admin")
            return 1

    should_start_legacy_user = user_only or (start_legacy_user and not admin_only)

    if not admin_only:
        if not (WEB_EMBEDDED / "index.html").is_file():
            log(f"缺少前端文件: {WEB_EMBEDDED}", "User")
            return 1

    ensure_data_dirs()
    if not check_python_deps():
        return 1

    if not user_only:
        try:
            init_database(force=init_db)
        except Exception as e:
            log(f"数据库初始化失败: {e}", "Admin")
            return 1

    flask_thread: threading.Thread | None = None
    user_thread: threading.Thread | None = None

    if not user_only:
        if not prepare_backend_port(backend_port, no_kill=no_kill_port):
            return 1

        if wait_admin_ready(backend_port, timeout=2):
            log(f"后台已在运行: {admin_url}", "Admin")
        else:
            log(f"启动后台（端口 {backend_port}，管理界面 + API + WebSocket）...", "Admin")
            flask_thread = start_flask_thread(backend_port, serve_static=True, static_ui="portal", host=host)
            if not wait_admin_ready(backend_port, timeout=backend_wait):
                log("后台启动失败", "Admin")
                return 1
            log("后台已就绪", "Admin")

        log_static_bundle("Portal", WEB_PORTAL)
        log_static_bundle("Admin", WEB_EMBEDDED_ADMIN)
        if wait_admin_ready(backend_port, timeout=2) and flask_thread is None:
            log("若管理界面未更新，请先 Ctrl+C 停止旧进程后重新运行 python main.py", "Admin")

        log(f"  统一门户: {admin_url}", "Portal")
        log(f"  教师端: {backend_url}/admin/", "Admin")
        log(f"  学生端: {backend_url}/student/", "User")
        log(f"  API 健康检查: {backend_url}/api/health", "Admin")

        try:
            sys.path.insert(0, str(BACKEND_DIR))
            from app.services.access_urls import build_access_urls

            access = build_access_urls(
                request_host=f"127.0.0.1:{backend_port}",
                port=backend_port,
            )
            if access.get("scan_ready"):
                log(f"  局域网主页（可制二维码）: {access['urls']['portal']}", "Portal")
                log("  （手机需与电脑同一 WiFi；请使用 --host 0.0.0.0 启动）", "Portal")
        except Exception:
            pass

    if should_start_legacy_user:
        if user_only and not wait_backend_ready(backend_url, timeout=backend_wait):
            log("后台未启动或不可用！", "User")
            log("请先运行: python main.py", "User")
            log(f"然后确认可访问: {backend_url}/api/health", "User")
            return 1

        write_user_api_config(backend_url)
        log_static_bundle("User", WEB_EMBEDDED)

        if not restart_user_frontend(user_port, no_kill=no_kill_port):
            return 1

        log(f"启动用户界面 http://127.0.0.1:{user_port}/", "User")
        log(f"API 后端地址: {backend_url.rstrip('/')}/api", "User")
        user_thread = start_user_http_thread(user_port, host=host)
        deadline = time.time() + backend_wait
        while time.time() < deadline:
            if frontend_ok(user_port):
                break
            time.sleep(0.3)
        else:
            log("用户界面启动失败", "User")
            return 1
        log("用户界面已就绪", "User")

        log(f"  兼容学生端: {user_url}", "User")
        log("测试账号: zhangsan / 123456 或 admin / admin123", "User")

    if not no_browser:
        if not user_only:
            webbrowser.open(admin_url)
        if should_start_legacy_user:
            webbrowser.open(user_url)

    log("按 Ctrl+C 停止服务", "TeamMind")

    try:
        while True:
            if flask_thread is not None and not flask_thread.is_alive():
                log("后台线程已退出", "Admin")
                return 1
            if user_thread is not None and not user_thread.is_alive():
                log("用户界面线程已退出", "User")
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        log("服务已停止", "TeamMind")
        return 0
