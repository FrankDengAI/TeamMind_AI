#!/usr/bin/env python3
"""验证嵌入式 UI 语言切换相关修复：模板 t() 包裹、英文词条、无错误包裹语法。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "student": ROOT / "web_embedded" / "assets" / "app.js",
    "admin": ROOT / "web_embedded_admin" / "assets" / "app.js",
}


def extract_template(text: str) -> str:
    start = text.find("  template: `")
    if start < 0:
        return ""
    start += len("  template: `")
    end = text.find("\n  `,", start)
    if end < 0:
        end = text.find("\n  `\n", start)
    return text[start:end] if end >= 0 else ""


def extract_t_keys(template: str) -> set[str]:
    keys = set(re.findall(r"t\('([^']+)'\)", template))
    keys.update(re.findall(r't\("([^"]+)"\)', template))
    return keys


def extract_text_i18n_en(source: str) -> dict[str, str]:
    m = re.search(r"const\s+\w+_TEXT_I18N\s*=\s*\{", source)
    if not m:
        return {}
    start = m.start()
    en = re.search(r"\ben:\s*\{", source[start:])
    if not en:
        return {}
    pos = start + en.end()
    depth = 1
    i = pos
    while i < len(source) and depth:
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    block = source[pos : i - 1]
    pairs = re.findall(r"(?:'((?:\\'|[^'])*)'|\"((?:\\\"|[^\"])*)\")\s*:\s*'((?:\\'|[^'])*)'", block)
    out: dict[str, str] = {}
    for a, b, val in pairs:
        key = (a or b).replace("\\'", "'")
        out[key] = val.replace("\\'", "'")
    return out


def main() -> int:
    failed = 0
    for name, path in FILES.items():
        text = path.read_text(encoding="utf-8")
        template = extract_template(text)
        bad_wrap = re.findall(r"'\{\{\s*t\(", template)
        broken_tag = re.findall(r"t\('[^']*</", template)
        keys = extract_t_keys(template)
        en = extract_text_i18n_en(text)
        missing = sorted(k for k in keys if k not in en and not re.match(r"^[a-zA-Z][\w.]*$", k))

        print(f"\n=== {name} ({path.name}) ===")
        print(f"  template t() keys: {len(keys)}")
        if bad_wrap:
            print(f"  FAIL broken wrap syntax: {len(bad_wrap)}")
            failed += 1
        else:
            print("  OK no broken '{{ t(' wrap syntax")
        if broken_tag:
            print(f"  FAIL broken HTML in t(): {broken_tag[:3]}")
            failed += 1
        else:
            print("  OK no HTML inside t() keys")
        if missing:
            print(f"  WARN missing en entries: {len(missing)} (first 8: {missing[:8]})")
        else:
            print("  OK all template t() keys have en entries or are structured keys")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
