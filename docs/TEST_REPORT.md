# 测试报告

## 测试环境

- OS: Windows / Linux
- Python 3.10+
- SQLite 内存 / 本地文件

## 自动化测试

```bash
pip install -r backend/requirements.txt
pytest -q
node --check web_portal/assets/portal.js
node --check web_embedded/assets/app.js
node --check web_embedded_admin/assets/app.js
```

### 用例覆盖

| 模块 | 文件 | 说明 |
|------|------|------|
| NLP | test_nlp_parser.py | 文本解析与短文本异常 |
| 分组 | test_grouping.py | 12人分组均衡性 |
| API | test_api_e2e.py | 健康检查、登录、画像、活动组队、权限边界 |
| 安全 | test_api_e2e.py | 学生越权导出、任务/报告教师操作、跨组访问和行为污染拦截 |

## 系统自检

```bash
python backend/scripts/self_check.py
```

检查项：健康检查、登录、文本解析、分组算法、看板同步、10 并发。

## 浏览器冒烟自检

```bash
python main.py --no-browser
python scripts/ui_smoke_test.py --base-url http://127.0.0.1:5000
```

覆盖统一门户语言切换、角色登录弹窗、教师端登录与导航、学生端登录与导航。

## 代码审查

```bash
python backend/scripts/code_review.py
```

生成 `docs/CODE_REVIEW_REPORT.md`（Ruff + Bandit）。

## 功能测试清单

- [x] 用户注册登录
- [x] 文本画像解析
- [x] 简历上传解析
- [x] 智能分组
- [x] 任务分配
- [x] 动态调优建议
- [x] 个人/团队看板
- [x] 管理员后台
- [x] 报告生成与导出
- [x] 学生越权访问和敏感导出拦截
- [x] 门户/教师端/学生端 UI 冒烟自检

## 已知警告

- SQLAlchemy `Query.get()` 仍有 2.x 迁移警告，后续可逐步替换为 `db.session.get()`。
- 测试环境使用开发密钥会触发 JWT HMAC key 长度警告；生产环境已要求通过环境变量设置强密钥。

## 性能（参考）

- 文本解析：< 2s（本地规则引擎）
- 分组 50 人：< 5s
- 10 并发健康检查：稳定 200
