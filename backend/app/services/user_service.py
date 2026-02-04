"""
用户相关服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.database import AsyncSessionLocal

async def get_user_by_username(username: str) -> User:
    """根据用户名获取用户"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        return user

async def create_user(username: str, password_hash: str, email: str = None, full_name: str = None, role: str = "user") -> User:
    """创建新用户"""
    async with AsyncSessionLocal() as session:
        new_user = User(
            username=username,
            password_hash=password_hash,
            email=email,
            full_name=full_name,
            role=role
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user