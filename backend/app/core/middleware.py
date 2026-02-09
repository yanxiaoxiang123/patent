"""中间件模块"""
import os
import time
from typing import Tuple
from collections import deque
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import RATE_LIMIT_WINDOW, RATE_LIMIT_MAX, RATE_LIMIT_LOGIN_MAX, MAX_BODY_SIZE
from app.core.redis_client import get_redis, RedisRateLimiter

# 内存回退速率限制（Redis 不可用时）
_fallback_storage = {}
_fallback_last_cleanup = 0.0
_fallback_cleanup_interval = 30.0
_fallback_max_keys = 200


async def check_rate_limit(request: Request, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int]:
    """
    检查速率限制（使用 Redis）

    Returns:
        (是否允许, 剩余请求数)
    """
    client_ip = request.client.host if request.client else "unknown"
    limit_key = f"ratelimit:{client_ip}"

    try:
        redis_client = await get_redis()
        limiter = RedisRateLimiter(redis_client)
        return await limiter.check_rate_limit(limit_key, max_requests, window_seconds)
    except Exception:
        # Redis 不可用时回退到内存限制
        return _fallback_check_rate_limit(limit_key, max_requests, window_seconds)


def _fallback_check_rate_limit(key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
    """内存回退速率限制"""
    global _fallback_last_cleanup
    current_time = time.time()
    window_start = current_time - window_seconds

    # 周期性清理过期 key，避免内存无限增长
    if current_time - _fallback_last_cleanup >= _fallback_cleanup_interval:
        keys_to_delete = []
        for k, timestamps in _fallback_storage.items():
            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()
            if not timestamps:
                keys_to_delete.append(k)
        for k in keys_to_delete:
            _fallback_storage.pop(k, None)
        _fallback_last_cleanup = current_time

    if key not in _fallback_storage:
        if len(_fallback_storage) >= _fallback_max_keys:
            return False, 0
        _fallback_storage[key] = deque()

    timestamps = _fallback_storage[key]
    # 清理旧请求记录
    while timestamps and timestamps[0] <= window_start:
        timestamps.popleft()

    # 检查是否超过限制
    current_count = len(timestamps)
    if current_count >= max_requests:
        return False, 0

    # 记录当前请求
    timestamps.append(current_time)
    return True, max_requests - current_count - 1


async def rate_limit_middleware(request: Request, call_next):
    """速率限制中间件 - 开发环境已禁用"""
    # 开发环境跳过速率限制
    if os.getenv("ENVIRONMENT", "development") == "development":
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = "unlimited"
        return response
    # 登录端点更严格的限制
    if request.url.path == "/api/auth/login":
        allowed, remaining = await check_rate_limit(request, RATE_LIMIT_LOGIN_MAX, RATE_LIMIT_WINDOW)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
                content={"detail": "请求过于频繁，请稍后再试"}
            )
    else:
        allowed, remaining = await check_rate_limit(request, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
                content={"detail": "请求过于频繁，请稍后再试"}
            )

    response = await call_next(request)
    # 添加速率限制响应头
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


async def request_size_limit_middleware(request: Request, call_next):
    """请求体大小限制中间件"""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > MAX_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "请求体过大，最大支持10MB"}
                )
        except ValueError:
            pass
    response = await call_next(request)
    return response


async def security_headers_middleware(request: Request, call_next):
    """安全响应头中间件"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response
