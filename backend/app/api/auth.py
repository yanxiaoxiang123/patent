"""认证 API 模块"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.core.security import create_token, parse_auth_header, TokenPayload
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.services.user_repository import UserRepository, get_user_dict_by_username
from app.utils.database import AsyncSessionLocal
from app.utils.passwords import hash_password, verify_password, needs_rehash
from app.models import User as UserModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["认证"])


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
    """获取当前用户"""
    token_payload: Optional[TokenPayload] = parse_auth_header(request.headers.get("Authorization"))
    if not token_payload:
        raise AuthenticationException("未认证或Token已过期")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, token_payload.user_id)

    if not user:
        raise AuthenticationException("用户不存在")

    if token_payload.username != user.username:
        raise AuthenticationException("用户信息已变更，请重新登录")

    user_dict = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }
    if not user_dict:
        raise AuthenticationException("用户不存在")

    return {
        "id": str(user_dict["id"]),
        "username": user_dict["username"],
        "role": user_dict["role"] or "user"
    }


async def get_current_user_model(request: Request) -> UserModel:
    """获取当前用户（ORM 模型）"""
    token_payload: Optional[TokenPayload] = parse_auth_header(request.headers.get("Authorization"))
    if not token_payload:
        raise AuthenticationException("未认证或Token已过期")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, token_payload.user_id)

    if not user:
        raise AuthenticationException("用户不存在")

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

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """用户登录"""
    logger.info(f"尝试登录用户: {user_data.username}")

    user_dict = await get_user_dict_by_username(user_data.username)

    if not user_dict:
        logger.warning(f"用户不存在: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名不存在"
        )

    user_id = user_dict["id"]
    username = user_dict["username"]
    password_hash = user_dict["password_hash"]
    role = user_dict["role"]

    if not verify_password(user_data.password, password_hash):
        logger.warning(f"密码错误: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误"
        )

    if needs_rehash(password_hash):
        try:
            async with AsyncSessionLocal() as session:
                user = await UserRepository.get_by_id(session, user_id)
                if user:
                    user.password_hash = hash_password(user_data.password)
                    await session.commit()
        except Exception as e:
            logger.warning(f"密码迁移失败: {user_data.username}, error={e}")

    logger.info(f"登录成功: {user_data.username}")

    access_token = create_token(user_id, username, role or "user")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": username,
            "email": None,
            "full_name": None,
            "role": role
        }
    }


@router.get("/me")
async def get_current_user_info():
    """获取当前用户信息"""
    return {"message": "认证API工作正常"}


@router.post("/logout")
async def logout():
    """用户登出（JWT Token 无需服务端存储，客户端删除Token即可）"""
    return {"message": "登出成功"}


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

        return {"data": users}


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

        return {"message": "创建成功", "user_id": user.id}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_admin: dict = Depends(require_admin)):
    """删除用户"""
    async with AsyncSessionLocal() as session:
        success = await UserRepository.delete(session, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"message": "删除成功"}
