from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from prince_archiver.definitions import Algorithm, EventType, System


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


class SrcDirInfo(BaseModel):
    local_path: Path
    img_count: int


class Checksum(BaseModel):
    hex: str
    algorithm: Algorithm = Algorithm.SHA256
