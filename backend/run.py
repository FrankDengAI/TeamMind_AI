"""TeamMind AI 后端启动入口."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TeamMind AI 后端")
    parser.add_argument("--no-static", action="store_true", help="不托管前端，仅 API")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    serve_static = not args.no_static
    app = create_app(serve_static=serve_static, static_ui="portal" if serve_static else None)
    if serve_static:
        print(f"[TeamMind] 浏览器访问: http://127.0.0.1:{args.port}/")
    else:
        print(f"[TeamMind] 仅 API: http://127.0.0.1:{args.port}/api/health")

    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False)
