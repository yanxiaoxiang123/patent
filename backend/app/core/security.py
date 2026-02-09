"""JWT Token 管理模块"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from pydantic import BaseModel

from app.core.config import TOKEN_SECRET

# Token 配置
TOKEN_EXPIRE_HOURS = 24  # Token 24小时过期
ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    """Token 载荷"""
    user_id: int
    username: str
    role: str
    exp: datetime
    iat: datetime


def create_token(user_id: int, username: str, role: str = "user") -> str:
    """创建 JWT Token"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=TOKEN_EXPIRE_HOURS)

    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, TOKEN_SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[TokenPayload]:
    """验证并解析 JWT Token"""
    try:
        payload = jwt.decode(token, TOKEN_SECRET, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解析 Token（不验证）"""
    try:
        return jwt.decode(token, TOKEN_SECRET, algorithms=[ALGORITHM], options={"verify_exp": False})
    except jwt.InvalidTokenError:
        return None


def parse_auth_header(auth_header: Optional[str]) -> Optional[TokenPayload]:
    """从 Authorization 头解析 Token"""
    if not auth_header:
        return None

    token = auth_header
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    return verify_token(token)
