"""Create database tables and seed initial users

安全说明：
- 种子密码在运行时随机生成并用 bcrypt 哈希，不再硬编码已知哈希
- 脚本执行后会在控制台打印初始密码，请立即记录并修改
- 如果用户已存在，不会覆盖密码（ON DUPLICATE KEY 仅更新角色）
"""
import asyncio
import secrets
import string
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from app.utils.database import engine, Base
from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.review import ReviewRecord
from app.utils.passwords import hash_password


def generate_password(length: int = 16) -> str:
    """生成随机强密码（包含大小写字母、数字、特殊字符）"""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # 确保至少包含各类字符
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%&*" for c in pwd)
        ):
            return pwd


async def main():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")

    # 生成随机密码
    yan_password = generate_password()
    admin_password = generate_password()

    yan_hash = hash_password(yan_password)
    admin_hash = hash_password(admin_password)

    # Seed users (仅在用户不存在时插入，已存在则只更新角色不覆盖密码)
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO users (username, password_hash, role, is_active, login_attempts) "
            "VALUES (:u1, :p1, :r1, 1, 0) "
            "ON DUPLICATE KEY UPDATE role=VALUES(role)"
        ), {"u1": "yan", "p1": yan_hash, "r1": "user"})
        await conn.execute(text(
            "INSERT INTO users (username, password_hash, role, is_active, login_attempts) "
            "VALUES (:u2, :p2, :r2, 1, 0) "
            "ON DUPLICATE KEY UPDATE role=VALUES(role)"
        ), {"u2": "admin", "p2": admin_hash, "r2": "admin"})

    print("=" * 50)
    print("初始用户已创建，请立即记录以下密码：")
    print(f"  yan   (user)  : {yan_password}")
    print(f"  admin (admin) : {admin_password}")
    print("=" * 50)
    print("⚠ 首次登录后请立即修改密码！")

    # Verify
    from sqlalchemy import select
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, username, role FROM users"))
        for row in result:
            print(f"  {row[0]}\t{row[1]}\t{row[2]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())