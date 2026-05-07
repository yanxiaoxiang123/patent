#!/usr/bin/env python3
"""
检查数据库中的测试用户
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from backend.app.models.user import User
from backend.app.utils.database import DATABASE_URL

async def check_database_users():
    """检查数据库中的用户"""
    print("🔍 检查数据库用户...")

    try:
        # 创建异步引擎和会话
        engine = create_async_engine(DATABASE_URL)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with AsyncSessionLocal() as session:
            # 检查表是否存在
            result = await session.execute(text("SHOW TABLES LIKE 'users'"))
            table_exists = result.fetchone()

            if not table_exists:
                print("❌ users 表不存在，需要先创建数据库表")
                return False

            # 查询所有用户
            result = await session.execute(select(User))
            users = result.scalars().all()

            print(f"📊 数据库中共有 {len(users)} 个用户:")
            for user in users:
                print(f"  👤 ID: {user.id}, 用户名: {user.username}, 角色: {user.role}")
                print(f"     邮箱: {user.email}, 全名: {user.full_name}")
                print(f"     创建时间: {user.created_at}")
                print()

            # 检查测试用户
            admin_user = None
            normal_user = None

            for user in users:
                if user.username == "admin":
                    admin_user = user
                elif user.username == "lizhuanyuan":
                    normal_user = user

            if admin_user:
                print("✅ 管理员用户 (admin) 存在")
            else:
                print("❌ 管理员用户 (admin) 不存在")

            if normal_user:
                print("✅ 普通用户 (lizhuanyuan) 存在")
            else:
                print("❌ 普通用户 (lizhuanyuan) 不存在")

            return len(users) > 0

    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False
    finally:
        await engine.dispose()

async def create_test_users():
    """创建测试用户"""
    print("🔧 创建测试用户...")

    try:
        from backend.app.utils.passwords import hash_password

        # 创建管理员用户
        admin_user = await create_user(
            username="admin",
            password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "admin123")),
            email="admin@example.com",
            full_name="系统管理员",
            role="admin"
        )
        print(f"✅ 创建管理员用户: {admin_user.username}")

        # 创建普通用户
        normal_user = await create_user(
            username="lizhuanyuan",
            password_hash=hash_password(os.getenv("USER_PASSWORD", "123456")),
            email="li@example.com",
            full_name="李专员",
            role="user"
        )
        print(f"✅ 创建普通用户: {normal_user.username}")

        return True

    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 智能专利辅助审核系统 - 数据库用户检查")
    print("="*60)

    # 检查现有用户
    has_users = await check_database_users()

    if not has_users:
        print("\n🔧 没有找到用户，开始创建测试用户...")
        success = await create_test_users()
        if success:
            print("\n✅ 测试用户创建成功，重新检查...")
            await check_database_users()
        else:
            print("\n❌ 测试用户创建失败")
    else:
        print("\n🎉 数据库用户检查完成")

if __name__ == "__main__":
    asyncio.run(main())
