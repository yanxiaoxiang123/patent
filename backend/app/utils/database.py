"""数据库模块"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("环境变量 DATABASE_URL 必须设置！请在 .env 文件中添加: DATABASE_URL=mysql+aiomysql://user:password@host:port/dbname")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


@asynccontextmanager
async def get_db():
    """依赖注入：获取数据库会话（带异常处理）"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_dependency():
    """FastAPI 依赖注入用的异步生成器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """关闭数据库连接池"""
    await engine.dispose()
