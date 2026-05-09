"""JWT Token 管理模块

安全机制：
- 每个 Token 携带唯一 JTI (JWT ID)，支持服务端撤销
- Token 有效期 2 小时（短生命周期降低泄露风险）
- TOKEN_SECRET 启动时校验最低强度（≥32 字符）
- Token 携带 token_version，用户密码变更或管理员强制下线时自动失效
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from pydantic import BaseModel

from app.core.config import TOKEN_SECRET

logger = logging.getLogger(__name__)

# Token 配置
TOKEN_EXPIRE_HOURS = 2  # Token 2小时过期（从 24h 缩短，降低泄露风险）
ALGORITHM = "HS256"

# 启动时校验 TOKEN_SECRET 强度
_MIN_SECRET_LENGTH = 32

if len(TOKEN_SECRET) < _MIN_SECRET_LENGTH:
    raise ValueError(
        f"TOKEN_SECRET 长度不足！当前 {len(TOKEN_SECRET)} 字符，"
        f"至少需要 {_MIN_SECRET_LENGTH} 字符。"
        "请在 .env 中设置更强的密钥，例如: "
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )


class TokenPayload(BaseModel):
    """Token 载荷"""
    user_id: int
    username: str
    role: str
    jti: str  # 唯一标识，用于撤销
    token_version: int = 0  # Token 版本号，用于批量失效
    exp: datetime
    iat: datetime


def create_token(
    user_id: int,
    username: str,
    role: str = "user",
    token_version: int = 0,
) -> str:
    """创建 JWT Token

    每个 Token 携带唯一 jti，可通过黑名单机制单独撤销。
    token_version 用于批量失效（如密码变更后所有旧 Token 失效）。
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=TOKEN_EXPIRE_HOURS)
    jti = uuid.uuid4().hex

    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "jti": jti,
        "token_version": token_version,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, TOKEN_SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[TokenPayload]:
    """验证并解析 JWT Token（仅做签名和过期校验，不检查黑名单）"""
    try:
        payload = jwt.decode(token, TOKEN_SECRET, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解析 Token（不验证过期，用于从已过期 Token 中提取信息）"""
    try:
        return jwt.decode(
            token, TOKEN_SECRET, algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return None


def extract_raw_token(auth_header: Optional[str]) -> Optional[str]:
    """从 Authorization 头中提取原始 Token 字符串"""
    if not auth_header:
        return None

    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return auth_header


def parse_auth_header(auth_header: Optional[str]) -> Optional[TokenPayload]:
    """从 Authorization 头解析 Token"""
    token = extract_raw_token(auth_header)
    if not token:
        return None

    return verify_token(token)
