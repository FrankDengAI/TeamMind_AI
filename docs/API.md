# 接口文档

Base URL: `http://localhost:5000/api`（开发时经 Vite 代理为 `/api`）

认证：除注册/登录/健康检查外，请求头需 `Authorization: Bearer <token>`

## 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/email/send-code` | 发送邮箱验证码 `{email, purpose: register\|reset_password}` |
| POST | `/auth/register/email` | 邮箱注册 `{email, code, name, password}` → `{token, user}` |
| POST | `/auth/register` | 旧版账号注册（生产可关闭 `TEAMMIND_ALLOW_LEGACY_REGISTER`） |
| POST | `/auth/login` | 登录 `{account, password}`，account 支持邮箱或账号 |
| POST | `/auth/forgot-password` | 忘记密码发验证码 `{email}` |
| POST | `/auth/reset-password` | 重置密码 `{email, code, new_password}` |
| POST | `/auth/change-password` | 修改密码（需 JWT） |
| GET | `/auth/me` | 当前用户 |
| PUT | `/auth/me` | 更新资料 |

用户字段含 `email`、`is_demo`、`email_verified`。演示账号 `is_demo=true` 不参与班级默认分组与催办统计。

### 管理端用户

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/users?exclude_demo=1` | 学员列表（默认排除演示；`include_demo=1` 含演示） |
| PATCH | `/admin/users/{id}` | 禁用/启用 `{status}` 或重置 `{password}` |
| POST | `/admin/users` | 创建教师 `{name, email, password, role: admin}` |
| POST | `/admin/classes/{id}/import` | CSV/Excel 批量导入班级成员 |
| POST | `/admin/ops/create-groups` | 智能分组，需 `class_id` 或 `user_ids` |

## 画像

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/profile/parse` | `{raw_text}` 文本解析 |
| POST | `/profile/submit` | `{raw_text/free_text, active_tags}` 主动标签 + DeepSeek 画像生成 |
| GET | `/profile/tags/catalog` | 获取三维主动标签库 |
| GET | `/profile/current` | 当前最新综合画像 |
| POST | `/profile/recalculate` | 根据被动标签和任务行为重算画像 |
| POST | `/profile/resume` | `multipart resume_file` |
| GET | `/profile/history` | 历史画像 |
| GET | `/profile/{id}` | 画像详情 |
| PUT | `/profile/{id}` | 手动修正 |

## 学习社区

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/community/feed` | 社区 Feed |
| POST | `/community/posts` | 发帖，支持 `multipart media`、标签、匿名 |
| GET | `/community/posts/{id}` | 帖子详情并记录浏览 |
| POST | `/community/posts/{id}/like` | 点赞并更新被动标签 |
| DELETE | `/community/posts/{id}/like` | 取消点赞 |
| POST | `/community/posts/{id}/favorite` | 收藏并更新被动标签 |
| POST | `/community/posts/{id}/comment` | 评论并更新被动标签 |

## 聊天

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/chat/conversations` | 会话列表 |
| POST | `/chat/conversations` | 创建/获取会话 `{target_user_id}` |
| GET | `/chat/conversations/{id}/messages` | 消息历史 |
| POST | `/chat/conversations/{id}/messages` | 发送消息 |
| POST | `/chat/conversations/{id}/read` | 标记已读 |

## 分组

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/group/create` | `{user_ids, group_size, config}` |
| GET | `/group/list` | 分组列表 |
| GET | `/group/{id}` | 分组详情 |
| PUT | `/group/{id}/members` | 手动调整成员 |

## 任务

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/task/assign` | `{group_id, template_key, team_goal}` |
| POST | `/task/adjust` | `{group_id}` 动态调优 |
| GET | `/task/list?group_id=` | 任务列表 |
| POST | `/task/{id}/progress` | `{progress, submit_status}` |
| POST | `/task/{id}/adjust/confirm` | `{accept: true/false}` |
| GET | `/task/templates` | 任务模板库 |

## 看板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/board/sync?group_id=` | 团队看板同步 |
| GET | `/board/personal` | 个人统计 |

## 报告与导出

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/report/generate` | `{group_id}` |
| GET | `/report/{group_id}` | 最新报告 |
| GET | `/export/{profile\|group\|task\|report}?format=xlsx\|pdf` | 导出 |

## 管理（需 admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/overview` | 总览 |
| GET | `/admin/users` | 用户列表 |
| GET/PUT | `/admin/config` | 系统配置 |
| GET/POST | `/admin/templates` | 任务模板 |
| GET | `/admin/community/posts` | 社区帖子审核列表 |
| PUT | `/admin/community/posts/{id}/status` | 隐藏/恢复帖子 |

## 状态码

## 角色与权限矩阵

| 角色 | 标识 | 数据范围 | 说明 |
|------|------|----------|------|
| 学员 | `role=user` | 已加入/待审批班级、本班活动与私聊 | `GET /classes` 仅返回与本人相关的班级；私聊需 `users_share_active_class` |
| 教师 | `role=admin` + `Classroom.teacher_id` | 本人任课班级与指挥舱指标 | 多教师按 `teacher_id` 隔离；`teacher_id=null` 的演示班仅首个 bootstrap 管理员可管 |
| 演示学员 | `is_demo=true` | 社区示例、演示班 | 不可 `join-request` 真实班；分组/预览/导出默认排除 |
| 禁用账号 | `status=disabled` | 无 | 改密或禁用后 `token_version` 递增，旧 JWT 立即失效 |

**教师督导旁路**：教师 JWT 访问学员 API（如小组看板、聊天）时保留只读/督导能力，见各路由内 `role==admin` 分支。

**管理端**：`PATCH /admin/users/{id}` 可设 `status` 或重置密码；`GET /admin/users` 默认 `exclude_demo=1`。

## 错误码

- 200 成功
- 400 参数错误
- 401 未认证
- 403 无权限
- 413 文件过大
- 415 格式不支持
- 422 解析失败
- 500 服务异常
