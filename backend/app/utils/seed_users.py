import argparse
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text

from app.utils.database import engine
from app.utils.passwords import hash_password


async def upsert_user(username: str, password: str, role: str) -> None:
    password_hash = hash_password(password)
    stmt = text(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (:username, :password_hash, :role)
        ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash),
            role = VALUES(role)
        """
    )
    async with engine.begin() as conn:
        await conn.execute(
            stmt,
            {"username": username, "password_hash": password_hash, "role": role},
        )


async def fetch_users(usernames: list) -> list:
    stmt = text(
        """
        SELECT id, username, role, created_at, updated_at
        FROM users
        WHERE username IN :usernames
        ORDER BY id ASC
        """
    ).bindparams(usernames=tuple(usernames))
    async with engine.begin() as conn:
        result = await conn.execute(stmt)
        rows = result.mappings().all()
        return [dict(r) for r in rows]


async def amain(args: argparse.Namespace) -> None:
    load_dotenv()
    try:
        await upsert_user("yan", args.yan_password, "user")
        await upsert_user("admin", args.admin_password, "admin")
        users = await fetch_users(["yan", "admin"])
        for u in users:
            print(f"{u['id']}\t{u['username']}\t{u['role']}")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yan-password", required=True, help="Password for 'yan' user")
    parser.add_argument("--admin-password", required=True, help="Password for 'admin' user")
    args = parser.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
