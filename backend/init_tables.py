"""Create database tables and seed test users"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from app.utils.database import engine, Base
from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.review import ReviewRecord

# SHA256 hashes
YAN_PASSWORD_HASH = "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
ADMIN_PASSWORD_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

async def main():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")

    # Seed users
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO users (username, password_hash, role, is_active, login_attempts) "
            "VALUES (:u1, :p1, :r1, 1, 0) "
            "ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash), role=VALUES(role)"
        ), {"u1": "yan", "p1": YAN_PASSWORD_HASH, "r1": "user"})
        await conn.execute(text(
            "INSERT INTO users (username, password_hash, role, is_active, login_attempts) "
            "VALUES (:u2, :p2, :r2, 1, 0) "
            "ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash), role=VALUES(role)"
        ), {"u2": "admin", "p2": ADMIN_PASSWORD_HASH, "r2": "admin"})
    print("Test users inserted: yan (user), admin (admin)")

    # Verify
    from sqlalchemy import select
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, username, role FROM users"))
        for row in result:
            print(f"  {row[0]}\t{row[1]}\t{row[2]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())