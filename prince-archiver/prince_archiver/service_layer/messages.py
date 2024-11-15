from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, Json

from prince_archiver.definitions import Algorithm, EventType, System
from prince_archiver.utils import now


class CommonImagingEvent(BaseModel):
    ref_id: UUID
    experiment_id: str
    timestamp: AwareDatetime
    type: EventType = Field(default=EventType.STITCH)
    system: System = Field(default=System.PRINCE)


# For importing imaging events into system
class SrcDirInfo(BaseModel):
    local_path: Path
    img_count: int


class ImagingEventStream(SrcDirInfo, CommonImagingEvent):
    metadata: Json[dict] | dict = Field(default_factory=dict)


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
    metadata: dict
    message_info: MessageInfo


class BaseSchema(BaseModel):
    pass


class Schema(CommonImagingEvent, BaseSchema):
    schema_version: Literal["0.1.0a1"] = "0.1.0a1"
    metadata: dict


class Checksum(BaseModel):
    hex: str
    algorithm: Algorithm = Algorithm.SHA256


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
