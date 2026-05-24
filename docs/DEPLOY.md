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

## 2.2 Zeabur 部署

不要把 DeepSeek Key、JWT 密钥或 Flask 密钥写入 `config.py`。在 Zeabur 项目的服务环境变量中配置：

| 变量 | 建议值 |
|------|--------|
| `TEAMMIND_ENV` | `production` |
| `SECRET_KEY` | 至少 32 位随机字符串 |
| `JWT_SECRET_KEY` | 至少 32 位随机字符串 |
| `TEAMMIND_CORS_ORIGINS` | 你的 Zeabur HTTPS 域名，例如 `https://your-app.zeabur.app` |
| `TEAMMIND_SOCKETIO_CORS_ORIGINS` | 同上 |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-chat` |
| `DEEPSEEK_ENABLED` | `1` |

Zeabur 通常会注入 `PORT` 环境变量；启动器会自动读取它。启动命令建议：

```bash
python main.py --host 0.0.0.0 --no-browser
```

如果平台需要拆分安装和启动命令：

```bash
pip install -r backend/requirements.txt
python main.py --host 0.0.0.0 --no-browser
```

部署完成后访问：

- `https://你的域名/`
- `https://你的域名/admin/`
- `https://你的域名/student/`
- `https://你的域名/api/health`

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
