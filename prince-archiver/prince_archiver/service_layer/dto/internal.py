from pathlib import Path
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, Json

from prince_archiver.utils import now

from .common import Checksum, CommonImagingEvent, Metadata, SrcDirInfo


class ImportImagingEvent(CommonImagingEvent):
    metadata: dict = Field(..., serialization_alias="raw_metadata")
    src_dir_info: SrcDirInfo


class ImportedImagingEvent(ImportImagingEvent):
    id: UUID


# For exporting out
class MessageInfo(BaseModel):
    id: str | bytes
    stream_name: str
    group_name: str


class ExportImagingEvent(CommonImagingEvent):
    local_path: Path
    metadata: Metadata
    message_info: MessageInfo


class ExportedImagingEvent(BaseModel):
    ref_id: UUID
    checksum: Json[Checksum] | Checksum
    size: int
    key: str
    timestamp: AwareDatetime = Field(default_factory=now)


# Relating to data archive
class ArchiveMember(BaseModel):
    member_key: str
    src_key: str


class AddDataArchiveEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    path: str
    job_id: UUID | None
    members: list[ArchiveMember]


class ArchivedImagingEvent(BaseModel):
    src_key: str
    data_archive_entry_id: UUID
