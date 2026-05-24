# 算法文档

## 0. 双标签画像评分

**文件**：`backend/app/services/profile_scoring.py`

用户画像不再只依赖关键词命中，而是融合：

- 主动标签：学生显式选择的知识、技能、协作标签
- LLM 解析：DeepSeek 对自由文本/简历/帖子内容的结构化 JSON
- 被动标签：点赞、收藏、评论、聊天等行为推断
- 任务行为：进度、活跃度、互评

综合公式见 `docs/PROFILE_TAGS.md`。

---

## 1. 异构分组算法

**文件**：`backend/app/services/algorithms/grouping.py`

### 输入
- 用户三维画像列表
- `group_size`（3-6，默认 4）
- `mode`：`heterogeneous` | `skill_focus`

### 步骤
1. 按 `skill_final`（兼容旧 `skill_score`）降序排序
2. 每组分配 1 名高技能种子（轮询）
3. 对其余用户计算互补增益并填入最优组
4. 均衡校验：组间技能均分差 ≤ 1.5，同 major ≤ 1 人
5. 局部 swap 微调（最多 20 轮）

### 互补增益公式

```
gain = skill_diversity - role_duplicate*2 - major_duplicate*3 + style_bonus
```

新版本额外加入主动/被动标签多样性：

```
gain += tag_diversity * 2.0
```

### 输出
- `groups[]`、`balance_score`、`complement_notes`、`audit_log`

### 测试用例
见 `backend/tests/test_grouping.py`：12 人分 3 组，技能差 ≤ 3。

---

## 2. 初始任务分配

**文件**：`backend/app/services/algorithms/task_assign.py`

### 规则
- 难度 ≈ 用户技能分（±2 容差）
- 角色匹配 `pref_role`
- 工时均衡（优先低负载用户）
- 依赖任务优先分配给高技能用户

---

## 3. 动态任务调优

**文件**：`backend/app/services/algorithms/task_adjust.py`

### 行为指标
- 进度完成率、提交时效、活跃次数、互评

### 调优策略
| 倾向 | 条件 | 动作 |
|------|------|------|
| positive | 进度≥80% | 提升难度 |
| negative | 进度≤40% 或多次逾期 | 降低难度 + 预警 |
| rebalance | 工时差>4h | 建议重新分配 |

### 调度
APScheduler 默认每 7 天执行，可通过 `/api/admin/config` 配置。

---

## 4. NLP 规则解析

**文件**：`backend/app/services/engines/nlp_parser.py`

关键词库见 `keyword_dict.py`，评分权重见 `config.py`。
