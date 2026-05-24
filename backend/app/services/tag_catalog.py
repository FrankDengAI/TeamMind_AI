"""画像标签库加载与匹配工具."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "tag_catalog.json"


@lru_cache(maxsize=1)
def load_tag_catalog() -> dict[str, list[dict[str, Any]]]:
    if not CATALOG_PATH.exists():
        return {"knowledge": [], "skill": [], "collab": []}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def flatten_tags() -> list[dict[str, Any]]:
    catalog = load_tag_catalog()
    out = []
    for dimension, tags in catalog.items():
        for tag in tags:
            out.append({**tag, "dimension": dimension})
    return out


def tag_by_name() -> dict[str, dict[str, Any]]:
    return {tag["name"]: tag for tag in flatten_tags()}


def normalize_active_tags(raw_tags: Any) -> list[dict[str, Any]]:
    """统一前端主动标签格式，兼容字符串、对象和按维度分组的对象."""
    if not raw_tags:
        return []
    items: list[Any] = []
    if isinstance(raw_tags, dict):
        for dimension, values in raw_tags.items():
            if not isinstance(values, list):
                continue
            for val in values:
                if isinstance(val, dict):
                    items.append({**val, "dimension": val.get("dimension") or dimension})
                else:
                    items.append({"name": str(val), "dimension": dimension})
    elif isinstance(raw_tags, list):
        items = raw_tags
    else:
        return []

    by_name = tag_by_name()
    normalized = []
    seen = set()
    for item in items:
        if isinstance(item, str):
            item = {"name": item}
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("label") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        catalog_tag = by_name.get(name, {})
        level = int(item.get("level") or 2)
        level = max(1, min(3, level))
        dimension = item.get("dimension") or catalog_tag.get("dimension") or "custom"
        weights = item.get("weights") or catalog_tag.get("weights") or _default_weights(dimension)
        normalized.append(
            {
                "id": item.get("id") or catalog_tag.get("id") or f"custom_{len(normalized) + 1}",
                "name": name,
                "dimension": dimension,
                "category": item.get("category") or catalog_tag.get("category") or "自定义",
                "level": level,
                "weights": weights,
                "custom": not bool(catalog_tag),
            }
        )
    return normalized


def _default_weights(dimension: str) -> dict[str, float]:
    if dimension == "knowledge":
        return {"knowledge": 0.7, "skill": 0.2, "collab": 0.1}
    if dimension == "skill":
        return {"knowledge": 0.1, "skill": 0.8, "collab": 0.1}
    if dimension == "collab":
        return {"knowledge": 0.05, "skill": 0.15, "collab": 0.8}
    return {"knowledge": 0.33, "skill": 0.33, "collab": 0.33}
