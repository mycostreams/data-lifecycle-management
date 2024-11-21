"""Messages propagating from external systems."""

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, Json

from .common import CommonImagingEvent, Metadata, SrcDirInfo


class NewImagingEvent(SrcDirInfo, CommonImagingEvent):
    metadata: Json[Metadata] | Metadata


# Messages emitted from Surf Data Archive
class NewDataArchiveEntries(BaseModel):
    job_id: UUID
    date: date
    archives: list["_Archive"]


class _Archive(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    path: str
    src_keys: list[str]
