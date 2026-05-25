# 部署文档（统一门户，本地存储，无 Docker）

## 环境要求

- Python 3.10+
- Windows 10+ 或 Linux/macOS
- Node.js 仅在使用 `frontend/` Vue 构建时可选；当前内置门户不需要前端构建

## 一、初始化

```powershell
cd teammind-ai
pip install -r backend/requirements.txt --index-url https://pypi.org/simple/
python database/init_db.py
```

## 二、统一入口启动（标准流程）

```powershell
python main.py
```

确认 http://127.0.0.1:5000/api/health 返回 `{"status":"ok"}`。

浏览器访问：

- 统一门户 http://127.0.0.1:5000/
- 教师端 http://127.0.0.1:5000/admin/
- 学生端 http://127.0.0.1:5000/student/

公网或局域网部署时建议只暴露 5000，并在前面接 HTTPS 反向代理：

```powershell
$env:TEAMMIND_ENV="production"
$env:SECRET_KEY="<至少32位随机字符串>"
$env:JWT_SECRET_KEY="<至少32位随机字符串>"
$env:TEAMMIND_CORS_ORIGINS="https://your-domain.example"
python main.py --host 0.0.0.0 --no-browser
```

| 入口 | 端口 | 说明 |
|------|------|------|
| main.py | 5000 | 统一门户 + 教师端 + 学生端 + API |

## 2.1 20 人答辩演示脚本

统一门户运行后，另开终端：

```powershell
python scripts/demo_flow_20students.py --reset
```

可选参数：`--group-size 5`（4 组 × 5 人）、`--base-url http://127.0.0.1:5000`。

脚本结束后打印各组名单与角色；用 `student01` / `123456` 进入 `/student/` 验证学员端。

## 2.2 Render 公网部署

Render 会注入环境变量 `PORT`（常见为 `10000`）和 `RENDER=true`。启动命令保持：

```bash
python main.py --host 0.0.0.0 --no-browser
```

**首次部署建议在 Render Dashboard → Environment 设置：**

| 变量 | 建议值（可先跑通） |
|------|-------------------|
| `TEAMMIND_ENV` | `development`（或 `production` 且必须配齐下列密钥） |
| `TEAMMIND_DISABLE_EMAIL_AUTH` | `1` |
| `TEAMMIND_ALLOW_LEGACY_REGISTER` | `1` |
| `TEAMMIND_PUBLIC_URL` | 你的 Render 公网 URL，如 `https://xxx.onrender.com` |

**正式上线** 将 `TEAMMIND_ENV` 改为 `production`，并设置 `SECRET_KEY`、`JWT_SECRET_KEY`、`TEAMMIND_CORS_ORIGINS`（填 Render 域名）。

**持久化数据库**：在 Render 为服务挂载 Disk，路径指向 `/opt/render/project/src/data`，否则每次部署会重新初始化 SQLite。

日志出现 `No open ports detected` / `Timed Out` 时，多为启动前执行了完整 `init_db.py` 导致迟迟不绑定 `PORT`。新版会先绑定端口，演示数据在后台导入；日志应出现 `Waitress 监听 0.0.0.0:10000`。

可选：导入仓库根目录 [`render.yaml`](../render.yaml) 作为 Blueprint 参考。

## 2.3 Zeabur 公网部署（逐步操作）

仓库已内置 Zeabur 构建配置，无需手动设置 `ZBPACK_*` 环境变量：

- [`zbpack.json`](../zbpack.json) — 构建与启动命令
- [`.env.example`](../.env.example) — 生产环境变量模板
- [`zeabur.template.yaml`](../zeabur.template.yaml) — 可选一键部署模板（含 Volume）

### 步骤 1：导入 GitHub 仓库

1. 打开 [Zeabur 控制台](https://zeabur.com/zh-CN/)
2. **Add Service** → **GitHub** → 选择 `FrankDengAI/TeamMind_AI`
3. Zeabur 会读取根目录 [`zbpack.json`](../zbpack.json) 自动安装依赖并执行 `python main.py --host 0.0.0.0 --no-browser`

### 步骤 2：配置环境变量

不要把 DeepSeek Key、JWT 密钥或 Flask 密钥写入 `config.py`。在 Zeabur **Variables** 面板添加（可参考 [`.env.example`](../.env.example)）：

| 变量 | 建议值 |
|------|--------|
| `TEAMMIND_ENV` | `production` |
| `SECRET_KEY` | 至少 32 位随机字符串 |
| `JWT_SECRET_KEY` | 至少 32 位随机字符串 |
| `TEAMMIND_CORS_ORIGINS` | 你的 Zeabur HTTPS 域名，例如 `https://your-app.zeabur.app` |
| `TEAMMIND_SOCKETIO_CORS_ORIGINS` | 同上 |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key（正式生产建议配置） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-chat` |
| `DEEPSEEK_ENABLED` | `1` |

> `TEAMMIND_ENV=production` 时缺少 `SECRET_KEY`、`JWT_SECRET_KEY` 或 `TEAMMIND_CORS_ORIGINS` 会导致服务启动失败。

### 步骤 3：绑定公网域名

1. 服务页 → **Networking / Domains** → 生成 `*.zeabur.app` 域名
2. 将完整 HTTPS 地址填入 `TEAMMIND_CORS_ORIGINS` 与 `TEAMMIND_SOCKETIO_CORS_ORIGINS`
3. 重新部署（Redeploy）

### 步骤 4：挂载持久化 Volume（正式生产必做）

Zeabur 容器默认无状态，不挂载 Volume 时 `data/teammind.db` 与上传文件会在重启后丢失。

1. 服务页 → **Volumes** → **Mount Volumes**
2. **Volume ID**：`data`
3. **Mount Directory**：`/src/data`
4. 保存并重启（首次挂载会清空该目录，随后自动初始化数据库）

### 步骤 5：验证部署

```bash
python scripts/verify_zeabur_deploy.py --base-url https://your-app.zeabur.app
```

部署完成后访问：

- `https://你的域名/`
- `https://你的域名/admin/`
- `https://你的域名/student/`
- `https://你的域名/api/health`

### 步骤 6：生产首次初始化（必做）

挂载 Volume 后数据库为空，**不要**在生产执行 `python main.py --init`（会清空库）。

在 Zeabur **Variables** 中建议增加：

| 变量 | 建议值 |
|------|--------|
| `TEAMMIND_DISABLE_DEMO_SEED` | `1`（关闭自动灌演示班级/帖子） |
| `TEAMMIND_ALLOW_LEGACY_REGISTER` | `0`（仅允许邮箱注册） |
| `TEAMMIND_EMAIL_DEV_MODE` | 开发可先 `1`；正式上线配置 SMTP 后设为 `0` |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` | 邮件验证码（QQ/163/Brevo 等免费 SMTP） |
| `TEAMMIND_PUBLIC_URL` | 你的 HTTPS 域名 |

在 Zeabur Shell（或本地连同一 Volume）创建首个管理员：

```bash
python scripts/bootstrap_production.py --email admin@your-school.edu --password "YourStr0ngPass1"
```

学员通过 `/student/` **邮箱注册**；教师仅由管理员创建或 bootstrap。

已有演示数据升级时（保留帖子/班级关联）：

```bash
python scripts/migrate_mark_demo_users.py
```

### 多教师与登录安全

- 每位教师仅能看到/操作 `Classroom.teacher_id` 为自己 ID 的班级；指挥舱 `GET /admin/dashboard` 按任课班级聚合。
- 学员端启动时会调用 `GET /auth/me` 校验会话；`role=admin` 或 `status=disabled` 会清空本地 token。
- 登录失败锁定为**单进程内存**计数（15 分钟内 5 次），多 worker 部署时各进程独立，生产建议前置网关限流或 Redis。

### 步骤 7：生产安全加固（可选）

若仍保留演示账号，请重置弱密码：

```bash
python scripts/reset_production_passwords.py --admin-password "你的强密码"
```

## 三、可选参数

**main.py**

- `--init` 重建数据库
- `--backend-port 5000` 修改统一门户/API 端口
- `--host 0.0.0.0` 允许公网或局域网访问
- `--no-kill-port` 不自动结束占用端口的进程（默认行为）
- `--kill-port` 仅开发调试时允许自动结束占用端口的旧进程
- `--no-browser` 不自动打开浏览器

**兼容入口**

- `python main_admin.py` 兼容入口：只启动后台与教师端
- `python main_user.py` 可选：单独启动学生端兼容入口，需后台已运行
- `--backend-url http://127.0.0.1:5000` 指定后台地址
- `--port 8080` 修改兼容学生端口
- `--wait 60` 等待后台就绪的最长时间（秒）

## 四、数据目录

| 路径 | 说明 |
|------|------|
| data/teammind.db | SQLite |
| data/uploads/ | 公开社区媒体 |
| data/private_uploads/resumes/ | 私有简历文件，不通过静态路由公开 |
| database/seeds/ | 教学演示虚构学生与帖子种子数据 |
| web_portal/ | 公网统一门户 |
| web_embedded_admin/ | 教师端 |
| web_embedded/ | 学生端 |
| web_embedded/assets/config.js | 学生端 API 地址（main_user 自动生成；5000 内置学生端默认使用 `/api`） |

## 五、常见问题

1. **main_user 提示后台未启动**  
   推荐先运行 `python main.py`，并确认 health 接口可访问；`main_user.py` 仅作为兼容入口保留。

2. **页面白屏**  
   按 F12 查看控制台；确认 CDN 可访问，或检查 `/assets/`、`/admin/assets/`、`/student/assets/` 是否可访问。

3. **想固定使用内置学生端或构建版学生端**  
   默认会在 `frontend/dist` 存在时优先使用构建版；可通过 `TEAMMIND_STUDENT_UI=embedded` 固定内置学生端，或用 `TEAMMIND_STUDENT_UI=dist` 明确使用构建版。

4. **DeepSeek 不生效**  
   公网部署前设置环境变量 `DEEPSEEK_API_KEY`；未配置时画像会降级为规则/标签分析，并在接口返回 `llm_error`。

## 六、生产安全清单

- 必须设置 `TEAMMIND_ENV=production`、`SECRET_KEY`、`JWT_SECRET_KEY`、`TEAMMIND_CORS_ORIGINS`。
- 默认演示账号 `admin/admin123`、学生账号 `123456` 只适合课堂演示；正式使用前请重置密码或关闭演示初始化。
- `python database/init_db.py` 会清空并重建数据库，只能用于首次演示或本地测试。
- 建议只暴露 HTTPS 反向代理后的 5000 入口，不直接暴露开发服务器到公网。
- `database/seeds/*.json` 为教学演示虚构数据，不代表真实学生信息。
