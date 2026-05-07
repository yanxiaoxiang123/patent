"""主应用模块 - FastAPI 应用入口"""
import uvicorn
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 配置日志 - 确保 INFO 级别能看到
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")  # backend/.env

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, CORS_ORIGINS
from app.core.middleware import (
    rate_limit_middleware,
    request_size_limit_middleware,
    security_headers_middleware,
)
from app.core.exceptions import global_exception_handler
from app.core.redis_client import close_redis
from app.utils.database import close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：数据库连接已准备好（通过 SQLAlchemy engine pool）
    yield
    # 关闭时：清理连接
    await close_redis()
    await close_db()


# 创建 FastAPI 应用
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 注册中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)
app.middleware("http")(request_size_limit_middleware)
app.middleware("http")(security_headers_middleware)

# 注册全局异常处理器
app.add_exception_handler(Exception, global_exception_handler)


# ===================== 健康检查端点 =====================

@app.get("/")
async def root():
    """根路径"""
    return {"message": "智能专利辅助审核系统 API", "status": "running"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "IPRS API"}


# ===================== 注册路由 =====================

from app.api import documents, auth, chat, admin

# 文档管理路由
app.include_router(documents.router, prefix="/api/documents", tags=["文档管理"])

# 认证路由 (包含管理员功能)
app.include_router(auth.router, prefix="/api/auth", tags=["认证管理"])

# AI 对话路由
app.include_router(chat.router, prefix="/api/ai", tags=["专利AI对话"])

# 管理员路由
app.include_router(admin.router, prefix="/api/admin", tags=["用户管理"])


# ===================== 启动入口 =====================

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=debug,
        log_level="info",
        access_log=True,
        use_colors=False
    )
