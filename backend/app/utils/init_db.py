import argparse
import asyncio

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

from app.utils.database import Base, engine


async def ensure_database_exists(database_url: str) -> None:
    import aiomysql

    url = make_url(database_url)
    db_name = url.database
    if not db_name:
        return

    conn = await aiomysql.connect(
        host=url.host or "localhost",
        port=url.port or 3306,
        user=url.username or "root",
        password=url.password or "",
        autocommit=True,
    )
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        if hasattr(conn, "ensure_closed"):
            await conn.ensure_closed()
        else:
            conn.close()


async def create_tables() -> None:
    import app.models as _models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def amain(args: argparse.Namespace) -> None:
    load_dotenv()

    database_url = args.database_url
    if database_url is None:
        import os

        database_url = os.getenv("DATABASE_URL", "")

    if not database_url:
        raise RuntimeError("DATABASE_URL 未配置")

    try:
        if not args.skip_create_db:
            await ensure_database_exists(database_url)
        await create_tables()
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--skip-create-db", action="store_true")
    args = parser.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
