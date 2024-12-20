from asyncpg.pool import PoolConnectionProxy
from fastapi import Depends
from starlette import status

from api.shemas.activity import ActivityOut, ActivityModel
from core.exceptions import NotFoundError
from api.endpoints.router import base_router
from core.db_manger import DBManager
from core.postgres_db import get_db


@base_router.get(
    "/{owner}/{repo}/activity",
    status_code=status.HTTP_200_OK,
)
async def get_activity(
        owner: str,
        repo: str,
        limit: int = 10,
        offset: int = 0,
        conn: PoolConnectionProxy = Depends(get_db)
) -> ActivityOut:
    db = DBManager(conn)

    repo_id = await db.get_repo_id_by_name_and_owner(owner=owner, repo=repo)
    if repo_id is None:
        raise NotFoundError(f"repo with owner = {owner} and name = {repo} not found")

    items: list[ActivityModel] = await db.get_activity(repo_id=repo_id, limit=limit, offset=offset)
    count = await db.get_activity_count(repo_id)
    return ActivityOut(items=items, count=count)
