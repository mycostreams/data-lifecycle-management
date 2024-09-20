from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from prince_archiver.definitions import Algorithm, EventType, System
from prince_archiver.utils import now


class CommonImagingEvent(BaseModel):
    ref_id: UUID
    experiment_id: str
    timestamp: datetime
    type: EventType = Field(default=EventType.STITCH)
    system: System = Field(default=System.PRINCE)


# For importing imaging events into system
class SrcDirInfo(BaseModel):
    staging_path: Path | None
    local_path: Path
    img_count: int
    raw_metadata: dict


class ImportImagingEvent(CommonImagingEvent):
    src_dir_info: SrcDirInfo


class ImagingEventStream(ImportImagingEvent):
    pass


class ImportedImagingEvent(ImportImagingEvent):
    id: UUID


# for exporting out
class ExportImagingEvent(CommonImagingEvent):
    staging_path: Path | None = None
    local_path: Path


class Checksum(BaseModel):
    hex: str
    algorithm: Algorithm = Algorithm.SHA256


class ExportedImagingEvent(BaseModel):
    ref_id: UUID
    checksum: Checksum
    size: int
    key: str
    timestamp: datetime = Field(default_factory=now)


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
