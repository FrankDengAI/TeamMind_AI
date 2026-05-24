#!/usr/bin/env bash
# TeamMind AI Linux/macOS 本地初始化
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ../database/init_db.py
cd "$ROOT"
echo "完成! 启动统一门户: python main.py"
echo "公网/局域网部署可用: python main.py --host 0.0.0.0 --no-browser"
