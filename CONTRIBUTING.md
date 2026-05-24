# 贡献指南

感谢关注组队超脑（TeamMind AI）！

## 开发流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更并确保通过测试：`python -m pytest -q backend/tests`
4. 运行自检：`python backend/scripts/self_check.py`（需先启动 `python main.py`）
5. 提交 Pull Request

## 代码规范

- Python：遵循 PEP8，使用 `ruff check app`
- Vue：使用 ESLint
- 核心算法与 API 需添加清晰注释

## 报告问题

请在 Issue 中提供：操作系统、复现步骤、期望与实际行为。
