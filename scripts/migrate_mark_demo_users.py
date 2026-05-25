#!/usr/bin/env python3
"""将已知演示/种子账号标记为 is_demo=true（不删除数据）."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app import create_app, db
from app.models import User

KNOWN_DEMO_ACCOUNTS = {
    "admin",
    "teacher",
    "zhangsan",
    "chenming",
    "linke",
    "jiangran",
    "tangyue",
    "qianqi",
    "demo_student",
    "演示同学01",
}

CLASS_PREFIXES = ("ai2401", "se2402", "ds2301", "dm2401")


def load_demo_accounts_from_json() -> set[str]:
    accounts = set(KNOWN_DEMO_ACCOUNTS)
    seeds = ROOT / "database" / "seeds" / "demo_students.json"
    if seeds.is_file():
        for item in json.loads(seeds.read_text(encoding="utf-8")):
            acc = (item.get("account") or "").strip()
            if acc:
                accounts.add(acc)
    for i in range(1, 21):
        accounts.add(f"student{i:02d}")
    for prefix in CLASS_PREFIXES:
        for i in range(1, 13):
            accounts.add(f"{prefix}_{i:02d}")
    return accounts


def main() -> int:
    app = create_app()
    demo_accounts = load_demo_accounts_from_json()
    with app.app_context():
        updated = 0
        for account in demo_accounts:
            user = User.query.filter_by(account=account).first()
            if user and not user.is_demo:
                user.is_demo = True
                updated += 1
        for user in User.query.all():
            parts = user.account.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit() and parts[0] in CLASS_PREFIXES:
                if not user.is_demo:
                    user.is_demo = True
                    updated += 1
        db.session.commit()
        print(f"已标记 is_demo=true 的账号数: {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
