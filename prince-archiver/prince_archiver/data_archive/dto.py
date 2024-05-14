from datetime import date
from uuid import UUID

from pydantic import BaseModel


class Archive(BaseModel):

    path: str
    src_keys: list[str]


class Message(BaseModel):

    job_id: UUID
    date: date
    archives: list[Archive]
