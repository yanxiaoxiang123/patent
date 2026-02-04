from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    email = Column(String(100), nullable=True, comment="邮箱")
    full_name = Column(String(100), nullable=True, comment="全名")
    role = Column(String(20), default="user", nullable=False, comment="角色: user/admin")
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    documents = relationship("Document", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# 数据库操作函数
async def get_user_by_username(username: str):
    """根据用户名获取用户"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

async def create_user(username: str, password_hash: str, email: str = None, full_name: str = None, role: str = "user"):
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

# 需要导入 AsyncSessionLocal
from app.utils.database import AsyncSessionLocal
