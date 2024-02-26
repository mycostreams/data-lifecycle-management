"""Definition of data transfer objects."""

from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class ExperimentDTO(BaseModel):

    id: str = Field(default_factory=str)
    plate: int
    cross_date: date = Field(..., alias="CrossDate")

    @model_validator(mode="after")
    def set_id(self) -> "ExperimentDTO":
        if not self.id:
            cross_date = self.cross_date.strftime("%Y")
            self.id = f"{cross_date}_{self.plate:02d}"
        return self


class BaseTimestepDTO(BaseModel):

    experiment: ExperimentDTO

    prince_position: int
    img_count: int
    timestamp: datetime

    raw_img_path: Path


class TimestepDTO(BaseTimestepDTO):

    experiment_archive_path: Path
    archive_name: str = Field(default_factory=str)

    @model_validator(mode="after")
    def set_archive_name(self) -> "TimestepDTO":
        if not self.archive_name:
            self.archive_name = self.timestamp.strftime("%Y%m%d_%H%M.tar.gz")
        return self

    @property
    def key(self) -> str:
        return f"{self.experiment.id}/{self.archive_name}"
