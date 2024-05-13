from datetime import date

from pydantic import BaseModel


class Archive(BaseModel):

    path: str
    src_keys: list[str]


class Message(BaseModel):

    job_id: str
    date: date
    archives: list[Archive]
