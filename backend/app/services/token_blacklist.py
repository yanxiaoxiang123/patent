"""Token 黑名单服务

提供基于 Redis 的 JWT Token 撤销机制：
- 单个 Token 撤销（通过 JTI）
- 使用 Redis SET + TTL 自动过期，无需手动清理
- Redis 不可用时回退到内存 LRU 缓存
"""
import logging
import time
from collections import OrderedDict
from typing import Optional

from app.core.config import TOKEN_SECRET  # noqa: F401 – 确保配置已加载
from app.core.security import TOKEN_EXPIRE_HOURS

logger = logging.getLogger(__name__)

# Redis key 前缀
_BLACKLIST_PREFIX = "token:blacklist:"

# Token 最大存活秒数（用于 Redis TTL 和内存清理）
_TOKEN_TTL_SECONDS = TOKEN_EXPIRE_HOURS * 3600

# 内存回退配置
_FALLBACK_MAX_SIZE = 10_000


class _InMemoryBlacklist:
    """内存回退黑名单（LRU 淘汰 + 过期清理）

    仅在 Redis 不可用时使用，重启后失效。
    """

    def __init__(self, max_size: int = _FALLBACK_MAX_SIZE) -> None:
        self._store: OrderedDict[str, float] = OrderedDict()
        self._max_size = max_size

    def add(self, jti: str, ttl_seconds: int) -> None:
        expire_at = time.time() + ttl_seconds
        if jti in self._store:
            self._store.move_to_end(jti)
        self._store[jti] = expire_at

        # 淘汰最旧的条目
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def contains(self, jti: str) -> bool:
        expire_at = self._store.get(jti)
        if expire_at is None:
            return False

        # 已过期则删除
        if time.time() > expire_at:
            del self._store[jti]
            return False

        return True

    def cleanup(self) -> int:
        """清理已过期条目，返回清理数量"""
        now = time.time()
        expired = [jti for jti, exp in self._store.items() if now > exp]
        for jti in expired:
            del self._store[jti]
        return len(expired)


# 单例内存回退
_fallback = _InMemoryBlacklist()


async def add_to_blacklist(jti: str, ttl_seconds: Optional[int] = None) -> None:
    """将 Token JTI 加入黑名单

    Args:
        jti: JWT Token 的唯一标识
        ttl_seconds: 黑名单保留时间（默认等于 Token 最大存活时间）
    """
    if ttl_seconds is None:
        ttl_seconds = _TOKEN_TTL_SECONDS

    try:
        from app.core.redis_client import get_redis

        redis_client = await get_redis()
        key = f"{_BLACKLIST_PREFIX}{jti}"
        await redis_client.setex(key, ttl_seconds, "1")
        logger.info("Token 已加入黑名单: jti=%s, ttl=%ds", jti, ttl_seconds)
    except Exception:
        logger.warning("Redis 不可用，使用内存黑名单: jti=%s", jti)
        _fallback.add(jti, ttl_seconds)


async def is_blacklisted(jti: str) -> bool:
    """检查 Token JTI 是否在黑名单中

    Args:
        jti: JWT Token 的唯一标识

    Returns:
        True 表示已撤销，不应接受该 Token
    """
    try:
        from app.core.redis_client import get_redis

        redis_client = await get_redis()
        key = f"{_BLACKLIST_PREFIX}{jti}"
        result = await redis_client.exists(key)
        if result:
            return True
    except Exception:
        logger.warning("Redis 不可用，使用内存黑名单检查: jti=%s", jti)

    # Redis 查不到或不可用时检查内存回退
    return _fallback.contains(jti)


async def blacklist_user_tokens(user_id: int) -> None:
    """标记某用户的所有 Token 需重新验证

    注意：此方法通过在 Redis 中设置 user-level 标记实现，
    配合 token_version 机制使用更佳（见 auth.py）。
    """
    try:
        from app.core.redis_client import get_redis

        redis_client = await get_redis()
        key = f"token:user_invalidate:{user_id}"
        await redis_client.setex(key, _TOKEN_TTL_SECONDS, str(int(time.time())))
        logger.info("已标记用户所有 Token 失效: user_id=%d", user_id)
    except Exception:
        logger.warning("Redis 不可用，无法批量失效用户 Token: user_id=%d", user_id)
