# 用户画像双标签体系

## 信号来源

画像由四类信号融合：

| 信号 | 来源 | 作用 |
| --- | --- | --- |
| 主动标签 | 学员选择的知识、技能、协作标签 | 表达显式能力与意图 |
| LLM 解析 | DeepSeek 对自由文本、简历、帖子内容的结构化分析 | 补足非关键词表达 |
| 被动标签 | 浏览、点赞、收藏、评论、聊天等行为 | 捕捉真实兴趣和协作倾向 |
| 任务行为 | 任务进度、活跃次数、互评 | 验证真实协作表现 |

## 综合评分公式

```text
Knowledge_final =
  0.30 * K_active + 0.30 * K_llm + 0.15 * K_passive + 0.15 * K_task + 0.10 * K_rule

Skill_final =
  0.35 * S_active + 0.30 * S_llm + 0.15 * S_passive + 0.20 * S_task

Collab_final =
  0.25 * C_active + 0.20 * C_llm + 0.30 * C_passive + 0.25 * C_task
```

权重理由：

- 知识和技能更依赖主动自报与文本证据，因此主动标签和 LLM 权重较高。
- 协作能力更需要从真实互动和任务行为中验证，因此被动标签与任务行为权重较高。
- 原关键词规则保留为兜底，只在知识维度占 10%，避免 DeepSeek 不可用时完全失效。

## 被动标签公式

```text
Δw_passive(t, e) = S_e * R(t, content_tags_e) * M_e * exp(-λ * Δdays)
w_passive(t) = min(1.0, w_passive(t) + Δw_passive(t, e))
```

- `S_e`：行为强度，收藏最高、点赞次之、浏览最低。
- `R`：行为对象标签与目标标签相关度。
- `M_e`：匿名内容降权，默认 0.7。
- `λ`：时间衰减系数，默认 0.05。

## DeepSeek 输出结构

DeepSeek 必须返回 JSON，核心字段包括：

```json
{
  "knowledge": {"score": 6.5, "tags": [], "major": "计算机", "degree": "本科", "evidence_quotes": []},
  "skill": {"score": 7.2, "tags": [], "tools": [], "evidence_quotes": []},
  "collaboration": {"score": 5.8, "pref_role": "技术开发", "styles": [], "comm_level": "中", "evidence_quotes": []},
  "custom_tags": [],
  "overall_confidence": 0.88
}
```
