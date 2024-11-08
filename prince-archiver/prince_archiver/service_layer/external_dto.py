"""Definition of data transfer objects."""

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# Messages emitted from Surf Data Archive
class Archive(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    path: str
    src_keys: list[str]


class UpdateArchiveEntries(BaseModel):
    job_id: UUID
    date: date
    archives: list[Archive]
