"""管理员 API 模块"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field

from app.core.security import parse_auth_header
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.services.user_repository import UserRepository
from app.utils.database import AsyncSessionLocal
from app.utils.passwords import hash_password, verify_password
from app.models import User as UserModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["管理员管理"])


# ===================== Pydantic Models =====================

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(min_length=6, max_length=100)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = Field(default="user", pattern=r'^(admin|user)$')


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern=r'^(admin|user)$')


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    role: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    last_login_at: Optional[str]
    last_login_ip: Optional[str]
    login_attempts: int
    created_at: Optional[str]


# ===================== 认证依赖 =====================

async def get_current_user(request: Request) -> dict:
    """获取当前用户"""
    from app.core.security import TokenPayload
    token_payload: Optional[TokenPayload] = parse_auth_header(request.headers.get("Authorization"))
    if not token_payload:
        raise AuthenticationException("未认证或Token已过期")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, token_payload.user_id)

    if not user:
        raise AuthenticationException("用户不存在")

    if token_payload.username != user.username:
        raise AuthenticationException("用户信息已变更，请重新登录")

    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role or "user"
    }


async def require_admin(request: Request) -> dict:
    """管理员权限校验"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise AuthorizationException("需要管理员权限")
    return user


# ===================== 管理员路由 =====================

@router.get("/users")
async def list_users(
    current_admin: dict = Depends(require_admin),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索用户名"),
    role: Optional[str] = Query(None, pattern=r'^(admin|user)$', description="角色筛选")
):
    """获取用户列表（支持分页、搜索、筛选）"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, or_, and_

        query = select(UserModel)

        # 搜索条件
        if search:
            query = query.where(UserModel.username.like(f"%{search}%"))

        # 角色筛选
        if role:
            query = query.where(UserModel.role == role)

        # 获取总数
        count_query = select(UserModel.id)
        if search:
            count_query = count_query.where(UserModel.username.like(f"%{search}%"))
        if role:
            count_query = count_query.where(UserModel.role == role)

        total_result = await session.execute(count_query)
        total = len(list(total_result.scalars().all()))

        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await session.execute(query)
        users_model = list(result.scalars().all())

        users = []
        for user in users_model:
            users.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "last_login_ip": user.last_login_ip,
                "login_attempts": user.login_attempts,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })

        return {
            "data": users,
            "meta": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size if total > 0 else 0
            }
        }


@router.post("/users")
async def create_user(payload: UserCreate, current_admin: dict = Depends(require_admin)):
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
            role=payload.role
        )

        return {
            "message": "创建成功",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }


@router.get("/users/{user_id}")
async def get_user(user_id: int, current_admin: dict = Depends(require_admin)):
    """获取单个用户"""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "last_login_ip": user.last_login_ip,
            "login_attempts": user.login_attempts,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }


@router.put("/users/{user_id}")
async def update_user(user_id: int, payload: UserUpdate, current_admin: dict = Depends(require_admin)):
    """更新用户"""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 如果要修改用户名，检查是否重复
        if payload.username and payload.username != user.username:
            exists = await UserRepository.username_exists(session, payload.username)
            if exists:
                raise HTTPException(status_code=400, detail="用户名已存在")

        # 更新字段
        update_data = payload.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        await session.commit()

        return {
            "message": "更新成功",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_admin: dict = Depends(require_admin)):
    """删除用户"""
    # 不能删除自己
    if int(current_admin["id"]) == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账户")

    async with AsyncSessionLocal() as session:
        success = await UserRepository.delete(session, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"message": "删除成功"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(user_id: int, payload: dict, current_admin: dict = Depends(require_admin)):
    """重置用户密码"""
    new_password = payload.get("password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.password_hash = hash_password(new_password)
        await session.commit()

        return {"message": "密码重置成功"}


@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: int, current_admin: dict = Depends(require_admin)):
    """切换用户启用/禁用状态"""
    # 不能操作自己
    if int(current_admin["id"]) == user_id:
        raise HTTPException(status_code=400, detail="不能修改当前登录账户的状态")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.is_active = not user.is_active
        await session.commit()

        status_text = "启用" if user.is_active else "禁用"
        return {"message": f"用户已{status_text}", "is_active": user.is_active}
