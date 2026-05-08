"""Redis 连接管理模块"""
import redis.asyncio as redis
from typing import Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# 连接池配置
REDIS_POOL_MAX_CONN = int(os.getenv("REDIS_POOL_MAX_CONN", "10"))

# 单例 Redis 客户端
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """获取 Redis 连接（依赖注入）"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=REDIS_DB,
            decode_responses=True,
            max_connections=REDIS_POOL_MAX_CONN,
        )
    return _redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class RedisRateLimiter:
    """Redis 速率限制器"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        检查速率限制

        Returns:
            (是否允许, 剩余请求数)
        """
        now = await self.redis.time()
        current_time = now[0]

        pipe = self.redis.pipeline()
        # 移除窗口外的旧记录
        pipe.zremrangebyscore(key, 0, current_time - window_seconds)
        # 添加当前请求
        pipe.zadd(key, {str(current_time): current_time})
        # 统计当前窗口内的请求数
        pipe.zcard(key)
        # 设置过期时间
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        current_count = results[2]
        remaining = max_requests - current_count

        if current_count > max_requests:
            return False, 0

        return True, max(0, remaining)

    async def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """获取剩余请求数"""
        now = await self.redis.time()
        current_time = now[0]

        # 清理过期记录并统计
        await self.redis.zremrangebyscore(key, 0, current_time - window_seconds)
        current_count = await self.redis.zcard(key)

        return max(0, max_requests - current_count)

    async def reset_key(self, key: str) -> bool:
        """重置速率限制键"""
        return await self.redis.delete(key)
