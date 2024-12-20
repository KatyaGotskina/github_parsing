from typing import Union

from asyncpg.pool import PoolConnectionProxy

from api.shemas.activity import ActivityModel
from core.exceptions import DBError
from api.shemas.repository import RepositoryModel


class DBManager:

    def __init__(self, connection: PoolConnectionProxy) -> None:
        self.connection = connection

    async def get_repositories(self, limit=100) -> list[RepositoryModel]:
        try:
            sequence = await self.connection.fetch("SELECT * FROM top100 LIMIT $1", limit)
        except Exception as err:
            raise DBError(err)

        return [RepositoryModel(
            repo=row['repo'],
            owner=row['owner'],
            position_cur=row['position_cur'],
            position_prev=row.get('position_prev'),
            stars=row['stars'],
            watchers=row['watchers'],
            open_issues=row['open_issues'],
            forks=row['forks'],
            language=row.get('language')
        ) for row in sequence]

    async def get_repo_id_by_name_and_owner(
            self,
            repo: str,
            owner: str,
    ) -> Union[int, None]:
        try:
            sequence = await self.connection.fetch(
                "SELECT id from top100 WHERE repo = $1 and owner = $2",
                f"{owner}/{repo}", owner
            )
        except Exception as err:
            raise DBError(err)

        if len(sequence) == 1:
            return sequence[0]['id']
        return None

    async def get_activity(
            self,
            repo_id: int,
            limit: int,
            offset: int
    ) -> list[ActivityModel]:
        try:
            sequence = await self.connection.fetch(
                """
                SELECT * FROM activity 
                WHERE activity.git_id = $1
                LIMIT $2
                OFFSET $3
                """,
                repo_id, limit, offset
            )
        except Exception as err:
            raise DBError(err)

        return [
            ActivityModel(
                commits=record['commits'],
                authors=record['authors'],
                date=record['date']
            ) for record in sequence
        ]

    async def get_activity_count(
            self,
            repo_id: int,
    ) -> int:
        try:
            sequence = await self.connection.fetch(
                """
                SELECT COUNT(*) AS count_for_git_id
                FROM activity
                WHERE git_id = $1;
                """,
                repo_id
            )
        except Exception as err:
            raise DBError(err)

        return sequence[0]['count_for_git_id']
