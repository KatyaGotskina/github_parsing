import asyncpg
from asyncpg.pool import PoolConnectionProxy

from core.config import settings


async def get_db() -> PoolConnectionProxy:
    pool = await asyncpg.create_pool(
        user=settings.DB_USER,
        host=settings.DB_HOST,
        password=settings.DB_PASSWORD
    )
    try:
        async with pool.acquire() as conn:
            yield conn
    finally:
        await pool.close()
