"""小组 config JSON 读写（含 member_roles）."""
import json
from typing import Any


def load_group_config(group) -> dict:
    if not group.config:
        return {}
    try:
        return json.loads(group.config)
    except (json.JSONDecodeError, TypeError):
        return {}


def save_group_config(group, cfg: dict) -> None:
    group.config = json.dumps(cfg, ensure_ascii=False)


def set_member_roles(group, roles: list[dict]) -> dict:
    cfg = load_group_config(group)
    cfg["member_roles"] = roles
    save_group_config(group, cfg)
    return cfg


def get_team_role(cfg: dict, user_id: int) -> str | None:
    for item in cfg.get("member_roles") or []:
        if int(item.get("user_id", -1)) == user_id:
            return item.get("role")
    return None
