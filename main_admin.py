#!/usr/bin/env python3
"""
组队超脑（TeamMind AI）后台入口（兼容保留）

推荐统一使用: python main.py

  python main_admin.py           # 仅启动后台与管理界面 (5000)
  python main_admin.py --init    # 重建数据库后启动
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from launch_utils import DEFAULT_BACKEND_PORT, launch_all, log  # type: ignore[reportMissingImports]  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="组队超脑（TeamMind AI）后台服务（含管理界面）")
    parser.add_argument("--init", action="store_true", help="强制重建数据库")
    parser.add_argument("--port", type=int, default=DEFAULT_BACKEND_PORT)
    parser.add_argument("--host", default="127.0.0.1", help="监听地址；公网部署可设为 0.0.0.0")
    parser.add_argument("--no-kill-port", action="store_true", help="端口被占用时不自动释放（默认行为）")
    parser.add_argument("--kill-port", action="store_true", help="开发调试时允许自动结束占用端口的旧进程")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    log("后台服务启动中...", "Admin")
    return launch_all(
        backend_port=args.port,
        init_db=args.init,
        no_kill_port=args.no_kill_port,
        kill_port=args.kill_port,
        no_browser=args.no_browser,
        admin_only=True,
        host=args.host,
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
