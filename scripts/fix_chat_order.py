#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "backend" / "app" / "api" / "chat.py"
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
new_block = [
    "    if not User.query.get(target):\n",
    '        return jsonify({"error": "目标用户不存在"}), 404\n',
    "    user = User.query.get(uid)\n",
    '    if not user or user.role != "admin":\n',
    "        if not users_share_active_class(uid, target):\n",
    '            return jsonify({"error": "仅可与同班学员私聊"}), 403\n',
]
for i, line in enumerate(lines):
    if line.startswith("def create_conversation"):
        lines[i + 7 : i + 12] = new_block
        break
text = "".join(lines)
while "    if False:\n" in text:
    text = text.replace("    if False:\n        return {\"error\": \"无权访问\"}\n", "")
p.write_text(text, encoding="utf-8")
print("ok")
