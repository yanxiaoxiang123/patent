#!/usr/bin/env python3
"""
直接创建测试用户 - 简化版本
"""
import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'db': os.getenv('DB_NAME', 'iprs'),
    'autocommit': True
}

if not DB_CONFIG['user'] or not DB_CONFIG['password']:
    raise RuntimeError("请设置环境变量 DB_USER 和 DB_PASSWORD")

async def create_test_users():
    """创建测试用户"""
    print("🔧 开始创建测试用户...")

    try:
        # 连接数据库
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()

        # 检查表是否存在
        await cursor.execute("SHOW TABLES LIKE 'users'")
        if not await cursor.fetchone():
            print("❌ users 表不存在，请先运行数据库初始化")
            return False

        # 检查是否已有测试用户
        await cursor.execute("SELECT username FROM users WHERE username IN ('admin', 'lizhuanyuan')")
        existing_users = await cursor.fetchall()

        if existing_users:
            print("📊 现有测试用户:")
            for user in existing_users:
                print(f"  👤 {user[0]}")
            print("\n✅ 测试用户已存在，无需创建")
            return True

        import hashlib
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        user_password = os.getenv("USER_PASSWORD", "123456")

        # 创建管理员用户
        await cursor.execute("""
            INSERT INTO users (username, password_hash, role, email, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, ("admin", hashlib.sha256(admin_password.encode()).hexdigest(), "admin", "admin@example.com", "系统管理员"))
        print("✅ 创建管理员用户: admin")

        # 创建普通用户
        await cursor.execute("""
            INSERT INTO users (username, password_hash, role, email, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, ("lizhuanyuan", hashlib.sha256(user_password.encode()).hexdigest(), "agent", "li@example.com", "李专员"))
        print("✅ 创建普通用户: lizhuanyuan")

        # 验证创建结果
        await cursor.execute("SELECT id, username, role FROM users WHERE username IN ('admin', 'lizhuanyuan')")
        users = await cursor.fetchall()

        print(f"\n🎉 成功创建 {len(users)} 个测试用户:")
        for user_id, username, role in users:
            print(f"  👤 ID: {user_id}, 用户名: {username}, 角色: {role}")

        await cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 智能专利辅助审核系统 - 创建测试用户")
    print("="*60)

    success = await create_test_users()

    if success:
        print("\n✅ 测试用户创建完成")
        print("\n🔑 测试账号信息:")
        print("  管理员: admin / (密码已哈希存储)")
        print("  普通用户: lizhuanyuan / (密码已哈希存储)")
        print("\n💡 提示: 现在可以重启后端服务并测试登录功能")
    else:
        print("\n❌ 测试用户创建失败，请检查数据库连接")

if __name__ == "__main__":
    asyncio.run(main())