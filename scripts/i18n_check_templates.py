#!/usr/bin/env python3
"""验证嵌入式 UI 模板中文是否已包裹 t()."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "web_embedded" / "assets" / "app.js",
    ROOT / "web_embedded_admin" / "assets" / "app.js",
]

TEMPLATE_START = "  template: `"
CHINESE = re.compile(r"[\u4e00-\u9fff]")


def extract_template(text: str) -> str:
    start = text.find(TEMPLATE_START)
    if start < 0:
        return ""
    start += len(TEMPLATE_START)
    end = text.find("\n  `,", start)
    if end < 0:
        end = text.find("\n  `\n", start)
    return text[start:end] if end >= 0 else ""


def find_unwrapped(template: str) -> list[str]:
    issues = []
    for i, line in enumerate(template.splitlines(), 1):
        if not CHINESE.search(line):
            continue
        if "{{" in line and "t(" in line:
            continue
        if ":label=\"t(" in line or ":placeholder=\"t(" in line:
            continue
        if "t('" in line or 't("' in line:
            continue
        # allow dynamic vue expressions with API data
        if "{{" in line and "}}" in line:
            if not re.search(r">\s*[\u4e00-\u9fff]", line):
                continue
        if line.strip().startswith("//"):
            continue
        issues.append(f"L{i}: {line.strip()[:120]}")
    return issues


def main() -> int:
    failed = 0
    for path in FILES:
        template = extract_template(path.read_text(encoding="utf-8"))
        issues = find_unwrapped(template)
        print(f"\n{path.name}: {len(issues)} potential unwrapped line(s)")
        for item in issues[:20]:
            print(f"  {item}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
        if issues:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
