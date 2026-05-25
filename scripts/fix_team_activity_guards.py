#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "backend" / "app" / "api" / "team_activity.py"
text = p.read_text(encoding="utf-8")
block = """    err = _admin_activity_guard(activity, get_request_user_id())
    if err:
        return err
"""
# Keep only when followed by admin-specific patterns or preceded by @admin_required
lines = text.splitlines(keepends=True)
out = []
i = 0
while i < len(lines):
    if lines[i] == "    err = _admin_activity_guard(activity, get_request_user_id())\n":
        # look back for @admin_required within 8 lines
        window = "".join(lines[max(0, i - 8) : i])
        if "@admin_required" in window:
            out.append(lines[i])
            out.append(lines[i + 1])
            out.append(lines[i + 2])
            i += 3
            continue
        i += 3
        continue
    out.append(lines[i])
    i += 1
p.write_text("".join(out), encoding="utf-8")
print("done")
