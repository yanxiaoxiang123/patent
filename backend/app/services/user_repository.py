"""用户仓储层 - 统一使用 SQLAlchemy"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User as UserModel
from app.utils.database import AsyncSessionLocal


class UserRepository:
    """用户数据访问仓储"""

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> Optional[UserModel]:
        """根据用户名获取用户"""
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[UserModel]:
        """根据 ID 获取用户"""
        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """获取所有用户"""
        result = await session.execute(
            select(UserModel)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "user"
    ) -> UserModel:
        """创建新用户"""
        user = UserModel(
            username=username,
            password_hash=password_hash,
            email=email,
            full_name=full_name,
            role=role
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def delete(session: AsyncSession, user_id: int) -> bool:
        """删除用户"""
        user = await UserRepository.get_by_id(session, user_id)
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False

    @staticmethod
    async def username_exists(session: AsyncSession, username: str) -> bool:
        """检查用户名是否存在"""
        result = await session.execute(
            select(UserModel.id).where(UserModel.username == username)
        )
        return result.scalar_one_or_none() is not None


# ===================== 便捷函数 =====================

async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """根据用户名获取用户（返回字典）"""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_username(session, username)
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "role": user.role,
                "is_active": user.is_active,
                "locked_until": user.locked_until,
                "login_attempts": user.login_attempts,
                "token_version": getattr(user, "token_version", 0) or 0,
            }
        return None


async def get_user_dict_by_username(username: str) -> Optional[Dict[str, Any]]:
    """根据用户名获取用户字典"""
    return await get_user_by_username(username)


async def create_user(
    username: str,
    password_hash: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: str = "user"
) -> UserModel:
    """创建新用户"""
    async with AsyncSessionLocal() as session:
        return await UserRepository.create(
            session, username, password_hash, email, full_name, role
        )
