from datetime import date
from uuid import UUID

from pydantic import BaseModel


class Archive(BaseModel):
    path: str
    src_keys: list[str]


class UpdateArchiveEntries(BaseModel):
    job_id: UUID
    date: date
    archives: list[Archive]


class DeleteExpiredUploads(BaseModel):
    job_id: UUID
    uploaded_on: date
