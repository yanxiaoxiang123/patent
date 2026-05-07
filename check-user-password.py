#!/usr/bin/env python3
"""
检查用户密码
"""
import asyncio
import os
from dotenv import load_dotenv
import aiomysql

load_dotenv()

async def check_user_passwords():
    """检查用户密码"""
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'db': os.getenv('DB_NAME', 'iprs'),
        'autocommit': True
    }

    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        print("❌ 请设置环境变量 DB_USER 和 DB_PASSWORD")
        return

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