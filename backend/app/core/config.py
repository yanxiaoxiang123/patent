"""应用核心配置模块"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# 确保加载 backend 目录下的 .env 文件
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# FastAPI 应用配置
APP_TITLE = "智能专利辅助审核系统 (IPRS)"
APP_DESCRIPTION = "基于 AI 的专利文档智能审核平台"
APP_VERSION = "1.0.0"

# CORS 配置
def parse_cors_origins() -> list:
    origins = os.getenv(
        "CORS_ORIGINS",
        '["http://localhost:3000", "http://localhost:8080", "http://localhost:3005", "http://127.0.0.1:3000", "http://127.0.0.1:8080", "http://127.0.0.1:3005"]',
    )
    if isinstance(origins, str):
        import json
        try:
            return json.loads(origins)
        except:
            return origins.strip("[]").replace(" ", "").replace('"', "").split(",")

CORS_ORIGINS = parse_cors_origins()

# 速率限制配置
RATE_LIMIT_WINDOW = 60  # 60秒
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "100"))
RATE_LIMIT_LOGIN_MAX = int(os.getenv("RATE_LIMIT_LOGIN_MAX", "5"))

# 请求体大小限制 (10MB)
MAX_BODY_SIZE = 10 * 1024 * 1024

# 数据库配置（必须通过环境变量设置）
DB_CONFIG = {
    'host': os.environ['DB_HOST'],
    'port': int(os.environ['DB_PORT']),
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'db': os.getenv('DB_NAME', 'iprs'),
    'autocommit': True
}

# Token 密钥（必须通过环境变量配置）
TOKEN_SECRET = os.getenv('TOKEN_SECRET')
if not TOKEN_SECRET:
    raise ValueError(
        "环境变量 TOKEN_SECRET 必须设置！"
        "请在 .env 文件中添加: TOKEN_SECRET=your-secure-secret-key"
    )

# Ollama 配置
def parse_ollama_urls() -> List[str]:
    """解析 Ollama 候选地址，保留配置顺序并补充本地回退地址。"""
    raw_urls = os.getenv("OLLAMA_URLS", "").strip()
    urls: List[str] = []

    if raw_urls:
        urls.extend([item.strip().rstrip("/") for item in raw_urls.split(",") if item.strip()])

    primary_url = os.getenv("OLLAMA_URL", "http://localhost:11434").strip().rstrip("/")
    if primary_url:
        urls.insert(0, primary_url)

    for fallback in ("http://localhost:11434", "http://127.0.0.1:11434"):
        if fallback not in urls:
            urls.append(fallback)

    deduped_urls: List[str] = []
    for url in urls:
        if url and url not in deduped_urls:
            deduped_urls.append(url)
    return deduped_urls


OLLAMA_URLS = parse_ollama_urls()
OLLAMA_URL = OLLAMA_URLS[0]
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# Redis 配置（可选，仅在启用限流时需要）
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_HOST else None)
