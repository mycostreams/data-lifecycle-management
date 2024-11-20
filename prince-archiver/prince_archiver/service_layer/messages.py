from datetime import datetime
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


class Application(BaseModel):
    application: str
    version: str
    user: str


class Camera(BaseModel):
    model: str
    station_name: str
    exposure_time: float
    frame_rate: float | None
    frame_size: tuple[int, int] | None
    binning: str
    gain: float | None
    gamma: float | None
    intensity: list[float]
    bits_per_pixel: float


class Stitching(BaseModel):
    last_focused_at: datetime | None
    grid_size: tuple[int, int]


class Metadata(BaseModel):
    application: Application
    camera: Camera
    stitching: Stitching | None = None


# Schemas for writing to file
class BaseSchema(BaseModel):
    pass


class Schema(CommonImagingEvent, BaseSchema):
    schema_version: Literal["0.1.0a1"]
    metadata: Metadata


# For importing imaging events into system
class SrcDirInfo(BaseModel):
    local_path: Path
    img_count: int


class ImagingEventStream(SrcDirInfo, CommonImagingEvent):
    metadata: Json[Metadata] | Metadata


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


class Checksum(BaseModel):
    hex: str
    algorithm: Algorithm = Algorithm.SHA256


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
