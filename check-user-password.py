#!/usr/bin/env python3
"""
检查用户密码
"""
import asyncio
import aiomysql

async def check_user_passwords():
    """检查用户密码"""
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123123',
        'db': 'iprs',
        'autocommit': True
    }

    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()

        await cursor.execute("SELECT username, password_hash FROM users")
        users = await cursor.fetchall()

        print("📊 数据库中的用户:")
        for username, password_hash in users:
            print(f"  👤 用户名: {username}, 密码: {password_hash}")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_passwords())