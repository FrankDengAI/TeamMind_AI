#!/usr/bin/env python3
"""
组队超脑（TeamMind AI）学员界面前台入口（兼容保留）

推荐统一使用: python main.py

  python main_user.py
  python main_user.py --backend-url http://127.0.0.1:5000
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from launch_utils import DEFAULT_BACKEND_URL, DEFAULT_USER_PORT, launch_all, log  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="组队超脑（TeamMind AI）用户界面")
    parser.add_argument("--port", type=int, default=DEFAULT_USER_PORT)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--host", default="127.0.0.1", help="监听地址；公网部署可设为 0.0.0.0")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-kill-port", action="store_true", help="端口被占用时不自动释放（默认行为）")
    parser.add_argument("--kill-port", action="store_true", help="开发调试时允许自动结束占用端口的旧进程")
    parser.add_argument("--wait", type=float, default=30, help="等待后台就绪秒数")
    args = parser.parse_args()

    parsed = urlparse(args.backend_url)
    backend_port = parsed.port or 5000

    log("用户界面启动中...", "User")
    return launch_all(
        backend_port=backend_port,
        user_port=args.port,
        no_kill_port=args.no_kill_port,
        kill_port=args.kill_port,
        no_browser=args.no_browser,
        user_only=True,
        backend_wait=args.wait,
        host=args.host,
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
