"""认证 API 模块

安全增强：
- 登录返回携带 JTI 和 token_version 的短有效期 Token
- 登出时将 Token JTI 加入 Redis 黑名单，服务端真正失效
- get_current_user 在每次请求时校验黑名单 + token_version
- 管理员可强制下线用户（递增 token_version）
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.core.security import (
    create_token,
    parse_auth_header,
    extract_raw_token,
    verify_token,
    TokenPayload,
    TOKEN_EXPIRE_HOURS,
)
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.services.user_repository import UserRepository, get_user_dict_by_username
from app.services.token_blacklist import add_to_blacklist, is_blacklisted
from app.utils.database import AsyncSessionLocal
from app.utils.passwords import hash_password, verify_password, needs_rehash
from app.models import User as UserModel
from app.schemas.response import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["认证"])

# 登录锁定配置
LOGIN_MAX_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


# ===================== Pydantic Models =====================

class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_]+$',
        description='用户名：3-50位，仅支持字母、数字、下划线'
    )
    password: str = Field(min_length=6, max_length=100, description='密码：6-100位')


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str
    user: dict


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    email: Optional[str] = None
    full_name: Optional[str] = None


# ===================== 认证依赖 =====================

async def get_current_user(request: Request) -> dict:
    """获取当前用户

    安全校验流程：
    1. 解析并验证 JWT 签名和过期时间
    2. 检查 Token JTI 是否在黑名单中（已登出/已撤销）
    3. 从数据库加载用户，验证用户是否存在且启用
    4. 比对 token_version 确保 Token 未被批量失效
    5. 比对 username 确保用户信息未变更
    """
    token_payload: Optional[TokenPayload] = parse_auth_header(
        request.headers.get("Authorization")
    )
    if not token_payload:
        raise AuthenticationException("未认证或Token已过期")

    # 检查 Token 是否已被撤销（黑名单）
    if await is_blacklisted(token_payload.jti):
        raise AuthenticationException("Token已失效，请重新登录")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, token_payload.user_id)

    if not user:
        raise AuthenticationException("用户不存在")

    # 检查 token_version 是否匹配（密码变更或管理员强制下线后失效）
    current_token_version = getattr(user, "token_version", 0) or 0
    if token_payload.token_version != current_token_version:
        raise AuthenticationException("Token已失效（凭证已变更），请重新登录")

    if token_payload.username != user.username:
        raise AuthenticationException("用户信息已变更，请重新登录")

    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role or "user",
    }


async def get_current_user_model(request: Request) -> UserModel:
    """获取当前用户（ORM 模型）"""
    token_payload: Optional[TokenPayload] = parse_auth_header(
        request.headers.get("Authorization")
    )
    if not token_payload:
        raise AuthenticationException("未认证或Token已过期")

    # 检查 Token 是否已被撤销
    if await is_blacklisted(token_payload.jti):
        raise AuthenticationException("Token已失效，请重新登录")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, token_payload.user_id)

    if not user:
        raise AuthenticationException("用户不存在")

    current_token_version = getattr(user, "token_version", 0) or 0
    if token_payload.token_version != current_token_version:
        raise AuthenticationException("Token已失效（凭证已变更），请重新登录")

    if token_payload.username != user.username:
        raise AuthenticationException("用户信息已变更，请重新登录")

    return user


async def require_admin(request: Request) -> dict:
    """管理员权限校验"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise AuthorizationException("需要管理员权限")
    return user


# ===================== 认证路由 =====================

@router.post("/login")
async def login(user_data: UserLogin, request: Request):
    """用户登录"""
    logger.info("尝试登录用户: %s", user_data.username)

    user_dict = await get_user_dict_by_username(user_data.username)

    if not user_dict:
        logger.warning("用户不存在: %s", user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名不存在"
        )

    user_id = user_dict["id"]
    username = user_dict["username"]
    password_hash = user_dict["password_hash"]
    role = user_dict["role"]
    is_active = user_dict.get("is_active", True)
    locked_until = user_dict.get("locked_until")
    login_attempts = user_dict.get("login_attempts", 0)
    token_version = user_dict.get("token_version", 0) or 0

    # 检查账户是否被禁用
    if not is_active:
        logger.warning("账户已被禁用: %s", user_data.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用，请联系管理员"
        )

    # 检查账户是否被锁定
    now = datetime.now()  # naive datetime for MySQL compatibility
    if locked_until:
        locked_until_naive = (
            locked_until.replace(tzinfo=None)
            if locked_until.tzinfo is not None
            else locked_until
        )
        if now < locked_until_naive:
            logger.warning("账户已被锁定: %s", user_data.username)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请稍后再试"
            )

    if not verify_password(user_data.password, password_hash):
        # 登录失败，记录失败次数
        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_id(session, user_id)
            if user:
                user.login_attempts = user.login_attempts + 1
                if user.login_attempts >= LOGIN_MAX_ATTEMPTS:
                    user.locked_until = datetime.now() + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )
                    logger.warning(
                        "账户已被锁定（连续失败%d次）: %s",
                        LOGIN_MAX_ATTEMPTS,
                        user_data.username,
                    )
                await session.commit()

        logger.warning("密码错误: %s", user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误"
        )

    # 登录成功，重置失败次数，更新最后登录信息
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if user:
            user.login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.now()
            user.last_login_ip = request.client.host if request.client else None
            await session.commit()

    if needs_rehash(password_hash):
        try:
            async with AsyncSessionLocal() as session:
                user = await UserRepository.get_by_id(session, user_id)
                if user:
                    user.password_hash = hash_password(user_data.password)
                    await session.commit()
        except Exception as e:
            logger.warning("密码迁移失败: %s, error=%s", user_data.username, e)

    logger.info("登录成功: %s", user_data.username)

    access_token = create_token(
        user_id, username, role or "user", token_version=token_version
    )

    return ApiResponse.ok({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_HOURS * 3600,
        "user": {
            "id": user_id,
            "username": username,
            "email": None,
            "full_name": None,
            "role": role
        }
    }).model_dump()


@router.post("/logout")
async def logout(request: Request):
    """用户登出 — 服务端撤销 Token

    将当前 Token 的 JTI 加入 Redis 黑名单，
    后续使用该 Token 的请求将被拒绝。
    """
    raw_token = extract_raw_token(request.headers.get("Authorization"))
    if not raw_token:
        # 未携带 Token 也返回成功（幂等性）
        return ApiResponse.ok(message="登出成功").model_dump()

    token_payload = verify_token(raw_token)
    if token_payload:
        # 计算 Token 剩余存活时间，作为黑名单 TTL
        now = datetime.now(timezone.utc)
        remaining_seconds = int((token_payload.exp - now).total_seconds())
        if remaining_seconds > 0:
            await add_to_blacklist(token_payload.jti, remaining_seconds)
            logger.info(
                "用户登出，Token 已撤销: user=%s, jti=%s",
                token_payload.username,
                token_payload.jti,
            )

    return ApiResponse.ok(message="登出成功").model_dump()


@router.get("/me")
async def get_current_user_info():
    """获取当前用户信息"""
    return {"message": "认证API工作正常"}


# ===================== 管理员路由 =====================

@router.get("/users")
async def list_users(current_admin: dict = Depends(require_admin)):
    """获取用户列表"""
    async with AsyncSessionLocal() as session:
        users_model = await UserRepository.get_all(session)

        users = []
        for user in users_model:
            users.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })

        return ApiResponse.ok({"users": users}, meta={"total": len(users)}).model_dump()


@router.post("/users")
async def create_user(payload: CreateUserRequest, current_admin: dict = Depends(require_admin)):
    """创建用户"""
    async with AsyncSessionLocal() as session:
        # 检查用户名是否存在
        exists = await UserRepository.username_exists(session, payload.username)
        if exists:
            raise HTTPException(status_code=400, detail="用户名已存在")

        hashed = hash_password(payload.password)

        user = await UserRepository.create(
            session,
            username=payload.username,
            password_hash=hashed,
            email=payload.email,
            full_name=payload.full_name,
            role="user"
        )

        return ApiResponse.ok({"user_id": user.id}, message="创建成功").model_dump()


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_admin: dict = Depends(require_admin)):
    """删除用户"""
    async with AsyncSessionLocal() as session:
        success = await UserRepository.delete(session, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        return ApiResponse.ok(message="删除成功").model_dump()


@router.post("/users/{user_id}/force-logout")
async def force_logout_user(user_id: int, current_admin: dict = Depends(require_admin)):
    """管理员强制下线用户

    递增用户的 token_version，使其所有已签发 Token 立即失效。
    """
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        current_version = getattr(user, "token_version", 0) or 0
        user.token_version = current_version + 1
        await session.commit()

        logger.info(
            "管理员强制下线用户: user_id=%d, new_token_version=%d",
            user_id,
            user.token_version,
        )

    return ApiResponse.ok(
        message=f"已强制下线用户 {user.username}，所有活跃Token已失效"
    ).model_dump()
