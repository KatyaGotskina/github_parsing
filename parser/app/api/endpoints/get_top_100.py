from asyncpg.pool import PoolConnectionProxy
from fastapi import Depends
from starlette import status

from api.endpoints.router import base_router
from api.shemas.repository import RepositoryModel
from core.db_manger import DBManager
from core.postgres_db import get_db


@base_router.get(
    "/top100",
    status_code=status.HTTP_200_OK,
)
async def get_top100(
        limit: int = 100,
        conn: PoolConnectionProxy = Depends(get_db)
) -> list[RepositoryModel]:
    db = DBManager(conn)
    return await db.get_repositories(limit=limit)
