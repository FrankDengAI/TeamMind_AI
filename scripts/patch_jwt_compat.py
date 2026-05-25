#!/usr/bin/env python3
"""将 API 中的 @jwt_required 替换为 jwt_required_compat（UTF-8 安全）."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app" / "api"


def patch_file(path: pathlib.Path) -> bool:
    if path.name in {"__init__.py", "auth.py"}:
        return False
    text = path.read_text(encoding="utf-8")
    if "@jwt_required" not in text and "jwt_required_compat" not in text:
        return False
    orig = text
    if "jwt_required_compat" not in text:
        if "from app.middleware.auth import jwt_required_compat" not in text:
            m = re.search(r"^from flask_jwt_extended import (.+)$", text, re.M)
            if m and "jwt_required_compat" not in m.group(1):
                imports = [x.strip() for x in m.group(1).split(",")]
                imports = [x for x in imports if x != "jwt_required"]
                new_line = "from flask_jwt_extended import " + ", ".join(imports)
                text = text[: m.start()] + new_line + "\nfrom app.middleware.auth import jwt_required_compat" + text[m.end() :]
            elif "from flask_jwt_extended import jwt_required" in text:
                text = text.replace(
                    "from flask_jwt_extended import jwt_required\n",
                    "from app.middleware.auth import jwt_required_compat\n",
                )
    text = text.replace("@jwt_required()", "@jwt_required_compat")
    text = text.replace(", jwt_required", "")
    text = text.replace("jwt_required, ", "")
    if "jwt_required_compat, jwt_required_compat" in text:
        text = text.replace("jwt_required_compat, jwt_required_compat", "jwt_required_compat")
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    n = 0
    for p in sorted(ROOT.glob("*.py")):
        if patch_file(p):
            print("patched", p.name)
            n += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
