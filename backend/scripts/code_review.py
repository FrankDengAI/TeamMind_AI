"""代码审查脚本 - 生成 CODE_REVIEW_REPORT.md."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT = ROOT / "docs" / "CODE_REVIEW_REPORT.md"
lines = [f"# 代码审查报告\n\n生成时间: {datetime.now().isoformat()}\n"]


def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return r.returncode, r.stdout + r.stderr
    except Exception as e:
        return 1, str(e)


def main():
    backend = ROOT / "backend"
    code, out = run("python -m ruff check app --output-format=concise", cwd=backend)
    lines.append(f"## PEP8 / Ruff\n\n```\n{out[:3000]}\n```\n状态: {'通过' if code == 0 else '需修复'}\n\n")

    code2, out2 = run("python -m bandit -r app -ll -q", cwd=backend)
    lines.append(f"## 安全 Bandit\n\n```\n{out2[:3000]}\n```\n状态: {'通过' if code2 == 0 else '有告警'}\n\n")

    lines.append("## 注释与可维护性\n\n- 核心算法与 NLP 引擎已添加模块级 docstring\n- API 按 Blueprint 模块化\n- 配置集中于 config.py\n\n")
    lines.append("## 依赖\n\n见 backend/requirements.txt，建议定期 pip audit\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已生成: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
