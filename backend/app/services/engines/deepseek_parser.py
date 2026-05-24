"""DeepSeek 语义画像解析器."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import Config
from app.services.tag_catalog import load_tag_catalog


class DeepSeekParser:
    """调用 DeepSeek，将自由文本解析成稳定 JSON 画像结构."""

    def parse_profile(self, free_text: str, active_tags: list[dict] | None = None) -> dict[str, Any]:
        if not Config.DEEPSEEK_ENABLED or not Config.DEEPSEEK_API_KEY:
            raise RuntimeError("DeepSeek 未配置")
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "free_text": free_text or "",
                        "active_tags": active_tags or [],
                        "tag_catalog": load_tag_catalog(),
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        payload = {
            "model": Config.DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        last_error = None
        for _ in range(2):
            try:
                with httpx.Client(timeout=Config.DEEPSEEK_TIMEOUT) as client:
                    resp = client.post(
                        Config.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions",
                        headers={
                            "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                return self._parse_json(content)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(f"DeepSeek 解析失败: {last_error}") from last_error

    def _parse_json(self, content: str) -> dict[str, Any]:
        content = (content or "").strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
        return self._validate(data)

    def _validate(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in ("knowledge", "skill", "collaboration"):
            data.setdefault(key, {})
            section = data[key]
            section["score"] = self._score(section.get("score"))
            section.setdefault("tags", [])
            section.setdefault("evidence_quotes", [])
        data["overall_confidence"] = max(0.0, min(1.0, float(data.get("overall_confidence") or 0.75)))
        data.setdefault("custom_tags", [])
        return data

    def _score(self, value) -> float:
        try:
            return round(max(0.0, min(10.0, float(value))), 1)
        except (TypeError, ValueError):
            return 5.0

    def _system_prompt(self) -> str:
        return (
            "你是一个用于高校协作学习平台的用户画像分析器。"
            "你的任务是结合用户主动标签和自由文本，提取知识、技能、协作三维画像。"
            "必须只输出 JSON，不要输出 markdown、解释、注释或多余文本。"
            "必须遵守字段结构："
            "{knowledge:{score:number,tags:[{name,level,confidence}],major,degree,evidence_quotes:[]},"
            "skill:{score:number,tags:[{name,level,confidence}],tools:[],evidence_quotes:[]},"
            "collaboration:{score:number,pref_role,styles:[],comm_level,evidence_quotes:[]},"
            "custom_tags:[{name,dimension,weight}],overall_confidence:number}。"
            "score 必须是 0-10；level 为 1了解、2熟练、3精通；confidence 为 0-1。"
            "只能根据文本和主动标签推断，证据不足时使用 null 或空数组，禁止编造经历。"
            "优先使用 tag_catalog 中已有标签；用户明显表达但词库没有的概念放入 custom_tags。"
            "学习场景下，知识分看学科理论和专业背景，技能分看工具与项目实操，协作分看沟通、角色偏好、团队经验。"
        )
