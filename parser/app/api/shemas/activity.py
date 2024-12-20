from datetime import date

from pydantic import BaseModel


class ActivityModel(BaseModel):
    commits: int
    authors: list[str]
    date: date


class ActivityOut(BaseModel):
    items: list[ActivityModel]
    count: int

