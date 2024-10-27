"""Definition of data transfer objects."""

from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from prince_archiver.definitions import EventType, System


class TimestepDTO(BaseModel):
    timestep_id: UUID = Field(default_factory=uuid4)

    plate: int
    cross_date: date
    experiment_id: str = Field(default_factory=str)

    timestamp: AwareDatetime
    event_type: EventType = EventType.STITCH
    system: System = System.PRINCE

    metadata: dict = Field(default_factory=dict)

    img_count: int = Field(150, alias="image_count")
    img_dir: Path = Field(..., alias="path")

    @model_validator(mode="after")
    def set_experiment_id(self) -> "TimestepDTO":
        if not self.experiment_id:
            cross_date = self.cross_date.strftime("%Y%m%d")
            self.experiment_id = f"{cross_date}_{self.plate:03d}"
        return self


# Messages emitted from Surf Data Archive
class Archive(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    path: str
    src_keys: list[str]


class UpdateArchiveEntries(BaseModel):
    job_id: UUID
    date: date
    archives: list[Archive]
