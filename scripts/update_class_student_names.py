#!/usr/bin/env python3
"""将班级演示学生「XX同学01」等占位姓名更新为真实中英文姓名，并修正 bio/headline。"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "teammind.db"
ROSTER_PATH = ROOT / "database" / "seeds" / "class_roster_names.json"

CLASS_META = {
    "dm2401": ("数字媒体技术", "2024", "交互媒体设计实践"),
    "ai2401": ("人工智能", "2024", "AI 产品创新实践"),
    "se2402": ("软件工程", "2024", "软件工程综合实训"),
    "ds2301": ("数据科学与大数据技术", "2023", "数据智能项目实践"),
}


def load_roster() -> dict:
    return json.loads(ROSTER_PATH.read_text(encoding="utf-8"))


def update_database(prefixes: list[str] | None = None) -> int:
    roster = load_roster()
    prefixes = prefixes or list(roster.keys())
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    updated = 0

    for prefix in prefixes:
        entries = roster.get(prefix)
        meta = CLASS_META.get(prefix)
        if not entries or not meta:
            print(f"跳过未知前缀: {prefix}", file=sys.stderr)
            continue
        major, grade, course = meta
        headline = f"{major} · {grade}级本科生"

        for idx, item in enumerate(entries, start=1):
            account = f"{prefix}_{idx:02d}"
            cur.execute("SELECT id FROM user WHERE account = ?", (account,))
            row = cur.fetchone()
            if not row:
                print(f"未找到账号: {account}")
                continue
            user_id = row["id"]
            cur.execute(
                """
                UPDATE user
                SET name = ?, headline = ?, bio = ?, research_interest = ?
                WHERE id = ?
                """,
                (item["name"], headline, item["bio"], item["research_interest"], user_id),
            )
            updated += cur.rowcount
            print(f"  {account} -> {item['name']}")

    conn.commit()
    conn.close()
    return updated


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    count = update_database(only)
    print(f"\n共更新 {count} 条用户记录。")
