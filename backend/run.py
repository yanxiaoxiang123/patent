#!/usr/bin/env python3
"""
FastAPI 应用启动脚本
用于开发和测试
"""
import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=debug,
        log_level="info"
    )