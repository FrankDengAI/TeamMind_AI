#!/usr/bin/env python3
"""将 Vue 模板中的硬编码中文替换为 {{ t('...') }} 或 :attr=\"t('...')\"."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "web_embedded" / "assets" / "app.js",
    ROOT / "web_embedded_admin" / "assets" / "app.js",
]

ATTRS = ("label", "placeholder", "title", "empty-text", "aria-label", "description", "active-text", "alt")
CHINESE = re.compile(r"[\u4e00-\u9fff]")
SKIP_ATTR = re.compile(r"\b(v-|@|:|#|ref=|key=|class=|style=|src=|href=|type=|name=|value=|size=|width=|min=|max=|rows=|stripe|plain|show-|divided|stretch|target=|alt=|for=|role=|id=|data-|v-model|v-if|v-else|v-for|loading|disabled|active|default)")


def escape_js(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def wrap_attr_line(line: str) -> str:
    for attr in ATTRS:
        pattern = re.compile(rf'(\s{attr})="([^"]*[\u4e00-\u9fff][^"]*)"')
        def repl(m):
            val = m.group(2)
            if "{{" in val or "t(" in val:
                return m.group(0)
            return f' :{attr}="t(\'{escape_js(val)}\')"'
        line = pattern.sub(repl, line)
    return line


def wrap_mixed_text(line: str) -> str:
    if "t('" in line or 't("' in line:
        return line

    def repl(m):
        prefix, expr, suffix = m.group(1), m.group(2), m.group(3)
        out = ""
        if prefix.strip() and CHINESE.search(prefix):
            out += "{{ t('" + escape_js(prefix.strip()) + "') }} "
        out += "{{ " + expr + " }}"
        if suffix.strip() and CHINESE.search(suffix):
            out += " {{ t('" + escape_js(suffix.strip()) + "') }}"
        return out

    return re.sub(
        r"([\u4e00-\u9fff][^{]*?)\{\{\s*(.+?)\s*\}\}([\u4e00-\u9fff：:，,。.！!？?％% ]*)",
        repl,
        line,
    )


def wrap_text_nodes(segment: str) -> str:
    parts = re.split(r"(<[^>]+>)", segment)
    out = []
    for part in parts:
        if part.startswith("<") or not CHINESE.search(part):
            out.append(part)
            continue
        if "{{" in part or "t(" in part:
            out.append(part)
            continue
        leading = re.match(r"^\s*", part).group(0)
        trailing = re.match(r".*?(\s*)$", part).group(1) if part.strip() else ""
        core = part.strip()
        if not core or not CHINESE.search(core):
            out.append(part)
            continue
        out.append(f"{leading}{{{{ t('{escape_js(core)}') }}}}{trailing}")
    return "".join(out)


def process_template(template: str) -> str:
    lines = template.split("\n")
    out = []
    for line in lines:
        if any(f'{a}="' in line for a in ATTRS):
            line = wrap_attr_line(line)
        if "{{" in line and CHINESE.search(line):
            line = wrap_mixed_text(line)
        if ">" in line and CHINESE.search(line):
            if line.strip().startswith("//"):
                out.append(line)
                continue
            if SKIP_ATTR.search(line) and not re.search(r">\s*[\u4e00-\u9fff]", line):
                out.append(line)
                continue
            line = wrap_text_nodes(line)
        out.append(line)
    return "\n".join(out)


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    marker = "  template: `"
    start = text.find(marker)
    if start < 0:
        print(f"skip (no template): {path}")
        return False
    start += len(marker)
    end = text.find("\n  `,", start)
    if end < 0:
        end = text.find("\n  `\n", start)
    if end < 0:
        print(f"skip (template end not found): {path}")
        return False
    original = text[start:end]
    updated = process_template(original)
    if updated == original:
        print(f"unchanged: {path}")
        return False
    path.write_text(text[:start] + updated + text[end:], encoding="utf-8")
    print(f"updated: {path}")
    return True


def main() -> int:
    changed = 0
    for target in TARGETS:
        if process_file(target):
            changed += 1
    print(f"done, {changed} file(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
