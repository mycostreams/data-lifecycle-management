from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from prince_archiver.definitions import EventType
from prince_archiver.domain.value_objects import (
    Checksum,
    GridSize,
)
from prince_archiver.utils import now


class ImagingParams(BaseModel):
    type: Literal[EventType.STITCH]
    grid_size: GridSize


class VideoParams(BaseModel):
    type: Literal[EventType.VIDEO]


ParamsT = Annotated[ImagingParams | VideoParams, Field(discriminator="type")]


# For importing imaging events into system
class ImportImagingEvent(BaseModel):
    ref_id: UUID
    experiment_id: str
    local_path: str
    timestamp: datetime
    type: EventType


class ImportedImagingEvent(ImportImagingEvent):
    id: UUID


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
    img_count: int
    size: int
    key: str
    timestamp: datetime = Field(default_factory=now)
