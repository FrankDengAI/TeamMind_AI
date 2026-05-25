#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "backend" / "app" / "api" / "group.py"
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
out = []
i = 0
patched = 0
while i < len(lines):
    if (
        patched < 2
        and lines[i].rstrip() == "    if not user_ids:"
        and i + 1 < len(lines)
        and "return jsonify" in lines[i + 1]
    ):
        out.append("    user_ids = _resolve_grouping_user_ids(data)\n")
        out.append("    if not user_ids:\n")
        out.append('        return jsonify({"error": "user_ids 不能为空"}), 400\n')
        out.append("\n")
        i += 2
        while i < len(lines) and lines[i].strip() != "profiles = []":
            i += 1
        patched += 1
        continue
    out.append(lines[i])
    i += 1
p.write_text("".join(out), encoding="utf-8")
print("patched", patched)
