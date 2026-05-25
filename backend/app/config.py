"""TeamMind AI 应用配置 - 本地 SQLite 与文件存储."""
import os
from pathlib import Path

# 项目根目录 teammind-ai/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def load_project_env(env_path: Path | None = None) -> bool:
    """加载项目根目录 .env（不覆盖已存在的环境变量）。"""
    path = env_path or (BASE_DIR / ".env")
    if not path.is_file():
        return False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value
    return True


load_project_env()

# Render / Zeabur 等未显式设置 TEAMMIND_ENV 时，避免生产校验缺密钥导致进程退出
if (os.environ.get("RENDER") or os.environ.get("ZEABUR")) and not os.environ.get("TEAMMIND_ENV"):
    os.environ.setdefault("TEAMMIND_ENV", "development")
DATA_DIR = BASE_DIR / "data"
UPLOAD_FOLDER = DATA_DIR / "uploads"
PRIVATE_UPLOAD_DIR = DATA_DIR / "private_uploads"
LOG_FOLDER = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "teammind.db"
LEGACY_DB_PATH = DATA_DIR / "teamforge.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
if not DB_PATH.exists() and LEGACY_DB_PATH.exists():
    LEGACY_DB_PATH.rename(DB_PATH)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PRIVATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_FOLDER.mkdir(parents=True, exist_ok=True)


def _csv_env(name: str, default: str = "*") -> list[str] | str:
    value = os.environ.get(name, default).strip()
    if value == "*":
        return "*"
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    """Flask 配置类."""

    APP_ENV = os.environ.get("TEAMMIND_ENV") or os.environ.get("FLASK_ENV") or "development"
    IS_PRODUCTION = APP_ENV.lower() in {"prod", "production"}
    SECRET_KEY = os.environ.get("SECRET_KEY", "teammind-dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 默认沿用升级前密钥，避免本地旧登录态在品牌迁移后全部失效
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "teamforge-jwt-secret")
    JWT_LEGACY_SECRET_KEYS = [
        item.strip()
        for item in os.environ.get("JWT_LEGACY_SECRET_KEYS", "teammind-jwt-secret").split(",")
        if item.strip()
    ]
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24h
    CORS_ORIGINS = _csv_env("TEAMMIND_CORS_ORIGINS", "*")
    SOCKETIO_CORS_ORIGINS = _csv_env("TEAMMIND_SOCKETIO_CORS_ORIGINS", os.environ.get("TEAMMIND_CORS_ORIGINS", "*"))

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = str(UPLOAD_FOLDER)
    PRIVATE_UPLOAD_FOLDER = str(PRIVATE_UPLOAD_DIR)
    RESUME_UPLOAD_FOLDER = str(PRIVATE_UPLOAD_DIR / "resumes")
    ALLOWED_RESUME_EXT = {".pdf", ".docx", ".doc"}

    # NLP 评分权重
    KNOWLEDGE_WEIGHT_DEGREE = 0.4
    KNOWLEDGE_WEIGHT_MAJOR = 0.3
    KNOWLEDGE_WEIGHT_THEORY = 0.3
    SKILL_WEIGHT_COUNT = 0.4
    SKILL_WEIGHT_PROJECT = 0.4
    SKILL_WEIGHT_DEPTH = 0.2
    COLLAB_WEIGHT_COMM = 0.3
    COLLAB_WEIGHT_ROLE = 0.25
    COLLAB_WEIGHT_STYLE = 0.25
    COLLAB_WEIGHT_EXP = 0.2

    # 分组默认参数
    DEFAULT_GROUP_SIZE = 4
    MAX_GROUP_USERS = 50
    BALANCE_SKILL_DIFF = 1.5

    # 任务调优周期（天）
    DEFAULT_ADJUST_DAYS = 7
    MAX_ADJUST_HISTORY = 10

    # 文本解析限制
    TEXT_MIN_LEN = 50
    TEXT_MAX_LEN = 800

    # DeepSeek 画像解析配置。公网部署必须通过环境变量注入密钥，避免把真实 Key 写入代码。
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_TIMEOUT = float(os.environ.get("DEEPSEEK_TIMEOUT", "15"))
    DEEPSEEK_ENABLED = os.environ.get("DEEPSEEK_ENABLED", "1") != "0"

    # 社区媒体上传限制
    MAX_POST_IMAGES = 9
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_VIDEO_SIZE = 50 * 1024 * 1024
    ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_VIDEO_EXT = {".mp4"}

    # 计费与支付（页面扫码 + 人工核销 MVP）
    BILLING_WECHAT_QR_URL = os.environ.get("BILLING_WECHAT_QR_URL", "")
    BILLING_ALIPAY_QR_URL = os.environ.get("BILLING_ALIPAY_QR_URL", "")
    BILLING_MANUAL_CONFIRM = os.environ.get("BILLING_MANUAL_CONFIRM", "1") != "0"
    BILLING_DEV_AUTO_PAY = os.environ.get("BILLING_DEV_AUTO_PAY", "0") != "0"
    BILLING_ORDER_TTL_MINUTES = int(os.environ.get("BILLING_ORDER_TTL_MINUTES", "30"))
    BILLING_WEBHOOK_SECRET = os.environ.get("BILLING_WEBHOOK_SECRET", "")

    # 演示种子与认证（生产默认关闭演示自动灌库）
    DISABLE_DEMO_SEED = os.environ.get("TEAMMIND_DISABLE_DEMO_SEED", "0") != "0"
    SEED_DEMO_ON_FIRST_BOOT = os.environ.get("TEAMMIND_SEED_DEMO_ON_FIRST_BOOT", "0") != "0"
    DEFER_DEMO_SEED = os.environ.get("TEAMMIND_DEFER_DEMO_SEED", "0") != "0"
    FAST_BOOT = os.environ.get("TEAMMIND_FAST_BOOT", "0") != "0"
    ALLOW_LEGACY_REGISTER = os.environ.get("TEAMMIND_ALLOW_LEGACY_REGISTER", "1") != "0"
    DISABLE_EMAIL_AUTH = os.environ.get("TEAMMIND_DISABLE_EMAIL_AUTH", "1") != "0"

    # 邮件 / 公网地址
    PUBLIC_URL = os.environ.get("TEAMMIND_PUBLIC_URL", "http://127.0.0.1:5000").rstrip("/")
    EMAIL_DEV_MODE = os.environ.get("TEAMMIND_EMAIL_DEV_MODE", "0") != "0"
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") != "0"
