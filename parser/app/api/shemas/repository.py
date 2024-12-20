from typing import Union

from pydantic import BaseModel


class RepositoryModel(BaseModel):
    repo: str
    owner: str
    position_cur: int
    position_prev: Union[int, None]
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: Union[str, None]

