"""Definition of data transfer objects."""

from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class TimestepMeta(BaseModel):

    timestep_id: UUID = Field(default_factory=uuid4)
    plate: int
    cross_date: date
    position: int
    timestamp: datetime
    img_count: int = 150
    img_dir: Path


class TimestepDTO(TimestepMeta):

    experiment_id: str = Field(default_factory=str)
    key: str = Field(default_factory=str)

    @model_validator(mode="after")
    def set_experiment_id(self) -> "TimestepDTO":
        if not self.experiment_id:
            cross_date = self.cross_date.strftime("%Y")
            self.experiment_id = f"{cross_date}_{self.plate:02d}"
        return self

    @model_validator(mode="after")
    def set_key(self) -> "TimestepDTO":
        if not self.key:
            root = self.timestamp.strftime("%Y%m%d_%H%M.tar")
            self.key = f"{self.experiment_id}/{root}"
        return self
