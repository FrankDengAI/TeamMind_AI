#!/usr/bin/env python3
"""用 exec 解析 JS 常量，验证 template 中 t() 键在 en 下是否仍含中文。"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent)
FILES = [
    ("student", ROOT / "web_embedded" / "assets" / "app.js", "STUDENT_I18N", "STUDENT_TEXT_I18N"),
    ("admin", ROOT / "web_embedded_admin" / "assets" / "app.js", "ADMIN_I18N", "ADMIN_TEXT_I18N"),
]


def extract_template(text: str) -> str:
    start = text.find("  template: `")
    start += len("  template: `")
    end = text.find("\n  `,", start)
    return text[start:end]


def build_node_script(prefix: str, structured_name: str, text_name: str, keys: list[str]) -> str:
    keys_json = __import__("json").dumps(keys, ensure_ascii=False)
    return f"""
{prefix}
const keys = {keys_json};
const structured = {structured_name};
const textI18n = {text_name};
const t = (typeof TeamMindI18n !== 'undefined')
  ? TeamMindI18n.createTranslator({{
      structuredI18n: structured,
      textI18n,
      getLang: () => 'en',
      getOpenCC: () => null,
    }})
  : (k) => k;
const untranslated = keys.filter((k) => /[\\u4e00-\\u9fff]/.test(String(t(k))));
console.log(JSON.stringify({{ total: keys.length, untranslated }}));
"""


def main() -> int:
    # load i18n-core
    core = (ROOT / "web_embedded" / "assets" / "i18n-core.js").read_text(encoding="utf-8")
    failed = 0
    for name, path, sn, tn in FILES:
        src = path.read_text(encoding="utf-8")
        template = extract_template(src)
        keys = sorted(set(re.findall(r"t\('([^']+)'\)", template)))
        prefix = src.split("const http = axios.create")[0]
        # remove Vue destructure line
        prefix = re.sub(r"^const \{ createApp.*\n", "", prefix, flags=re.M)
        script = core + "\n" + build_node_script(prefix, sn, tn, keys)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(script)
            tmp = f.name
        r = subprocess.run(["node", tmp], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(f"\n=== {name} ERROR ===")
            print(r.stderr[:500])
            failed += 1
            continue
        import json
        data = json.loads(r.stdout.strip())
        print(f"\n=== {name} ===")
        print(f"  template t() keys: {data['total']}")
        print(f"  still Chinese in en: {len(data['untranslated'])}")
        if data["untranslated"]:
            failed += 1
            for k in data["untranslated"][:25]:
                print(f"    - {k}")
            if len(data["untranslated"]) > 25:
                print(f"    ... +{len(data['untranslated']) - 25} more")
        else:
            print("  OK all template strings translate to English")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
