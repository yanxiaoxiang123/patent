#!/usr/bin/env python3
"""
直接创建测试用户 - 简化版本
"""
import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123123',
    'db': 'iprs',
    'autocommit': True
}

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

        # 创建管理员用户
        await cursor.execute("""
            INSERT INTO users (username, password_hash, role, email, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, ("admin", "admin123", "admin", "admin@example.com", "系统管理员"))
        print("✅ 创建管理员用户: admin")

        # 创建普通用户
        await cursor.execute("""
            INSERT INTO users (username, password_hash, role, email, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, ("lizhuanyuan", "123456", "agent", "li@example.com", "李专员"))
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
        print("  管理员: admin / admin123")
        print("  普通用户: lizhuanyuan / 123456")
        print("\n💡 提示: 现在可以重启后端服务并测试登录功能")
    else:
        print("\n❌ 测试用户创建失败，请检查数据库连接")

if __name__ == "__main__":
    asyncio.run(main())