#!/usr/bin/env python3
"""深度检查模板：找出仍含中文但未走 t() 的行，以及 t() 键缺少英文翻译的项。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "web_embedded" / "assets" / "app.js",
    ROOT / "web_embedded_admin" / "assets" / "app.js",
]
CHINESE = re.compile(r"[\u4e00-\u9fff]")
STRUCTURED_KEY = re.compile(r"^[a-zA-Z][\w.]*$")


def extract_template(text: str) -> str:
    start = text.find("  template: `")
    if start < 0:
        return ""
    start += len("  template: `")
    end = text.find("\n  `,", start)
    if end < 0:
        end = text.find("\n  `\n", start)
    return text[start:end] if end >= 0 else ""


def extract_en_dict(source: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?:Object\.assign\(\w+\.en,\s*\{|^\s*en:\s*\{)", source, re.M):
        pos = m.end()
        depth = 1
        i = pos
        while i < len(source) and depth:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        block = source[pos : i - 1]
        for km in re.finditer(
            r"(?:'((?:\\'|[^'])*)'|\"((?:\\\"|[^\"])*)\")\s*:\s*'((?:\\'|[^'])*)'",
            block,
        ):
            key = (km.group(1) or km.group(2)).replace("\\'", "'")
            val = km.group(3).replace("\\'", "'")
            out[key] = val
    return out


def extract_structured_en(source: str) -> set[str]:
    keys: set[str] = set()
    m = re.search(r"en:\s*\{", source)
    if not m:
        return keys
    pos = m.end()
    depth = 1
    i = pos
    while i < len(source) and depth:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    block = source[pos : i - 1]
    for km in re.finditer(r"\b([a-zA-Z][\w]*)\s*:", block):
        keys.add(km.group(1))
    return keys


def unwrapped_lines(template: str) -> list[str]:
    issues = []
    for i, line in enumerate(template.splitlines(), 1):
        if not CHINESE.search(line):
            continue
        if line.strip().startswith("<!--"):
            continue
        if "t('" in line or 't("' in line:
            continue
        if ":label=\"t(" in line or ":placeholder=\"t(" in line or ":empty-text=\"t(" in line:
            continue
        if ":description=\"t(" in line or ":active-text=\"t(" in line:
            continue
        if "{{" in line and "}}" in line and not re.search(r">\s*[\u4e00-\u9fff]", line):
            continue
        issues.append(f"L{i}: {line.strip()[:140]}")
    return issues


def missing_en(template: str, en: dict[str, str], structured: set[str]) -> list[str]:
    keys = set(re.findall(r"t\('([^']+)'\)", template))
    keys.update(re.findall(r't\("([^"]+)"\)', template))
    missing = []
    for k in sorted(keys):
        if STRUCTURED_KEY.match(k) and k in structured:
            continue
        if k not in en:
            missing.append(k)
    return missing


def main() -> int:
    failed = 0
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        template = extract_template(text)
        en = extract_en_dict(text)
        structured = extract_structured_en(text)
        bad = unwrapped_lines(template)
        miss = missing_en(template, en, structured)

        print(f"\n=== {path.relative_to(ROOT)} ===")
        print(f"  template lines: {len(template.splitlines())}")
        t_keys = set(re.findall(r"t\('([^']+)'\)", template))
        print(f"  t() keys: {len(t_keys)}")
        print(f"  en dict entries (merged): {len(en)}")

        if bad:
            print(f"  FAIL unwrapped Chinese lines: {len(bad)}")
            for x in bad[:15]:
                print(f"    {x}")
            if len(bad) > 15:
                print(f"    ... +{len(bad) - 15} more")
            failed += 1
        else:
            print("  OK all Chinese in template uses t()")

        if miss:
            print(f"  WARN missing en for {len(miss)} t() keys:")
            for x in miss[:20]:
                print(f"    - {x}")
            if len(miss) > 20:
                print(f"    ... +{len(miss) - 20} more")
        else:
            print("  OK all t() keys have en translations")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
