from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from prince_archiver.definitions import EventType
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.utils import now


# For importing imaging events into system
class ImportImagingEvent(BaseModel):
    ref_id: UUID
    experiment_id: str
    local_path: Path
    timestamp: datetime
    type: EventType


class ImportedImagingEvent(ImportImagingEvent):
    id: UUID


class AddSrcDirInfo(BaseModel):
    ref_id: UUID
    img_count: int
    raw_metadata: dict


# For Exporting events out
class InitiateExportEvent(BaseModel):
    ref_id: UUID
    type: EventType


class ExportImagingEvent(BaseModel):
    ref_id: UUID
    type: EventType
    local_path: Path
    target_key: str


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
