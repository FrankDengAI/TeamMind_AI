#!/usr/bin/env python3
"""
组队超脑（TeamMind AI）统一启动入口

  python main.py              # 启动统一门户 + 教师端 + 学生端 + API (5000)
  python main.py --init       # 重建数据库后启动
  python main.py --no-browser # 不自动打开浏览器
  python main.py --host 0.0.0.0 # 允许局域网访问；手机同 WiFi 扫 /scan/ 二维码进入

端口与前端（不由本文件定义 UI，仅托管静态目录）：
  5000  统一门户 + 教师端 + 学生端 + API + WebSocket

前端功能：
  学员端：主动/被动标签、学习社区、消息、综合画像
  管理端：学员画像明细、社区管理
  启动后侧边栏应显示版本号；若无请 Ctrl+F5 强刷
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from launch_utils import (  # type: ignore[reportMissingImports]  # noqa: E402
    DEFAULT_BACKEND_PORT,
    launch_all,
    log,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="组队超脑（TeamMind AI）统一启动")
    parser.add_argument("--init", action="store_true", help="强制重建数据库")
    parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT)
    parser.add_argument("--host", default="127.0.0.1", help="监听地址；公网部署可设为 0.0.0.0")
    parser.add_argument("--no-kill-port", action="store_true", help="端口被占用时不自动释放（默认行为）")
    parser.add_argument("--kill-port", action="store_true", help="开发调试时允许自动结束占用端口的旧进程")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    log("组队超脑（TeamMind AI）启动中（统一门户 + 双端工作台）...", "Main")
    return launch_all(
        backend_port=args.backend_port,
        init_db=args.init,
        no_kill_port=args.no_kill_port,
        kill_port=args.kill_port,
        no_browser=args.no_browser,
        host=args.host,
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
