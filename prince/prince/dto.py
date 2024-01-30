"""Definition of data transfer objects."""

from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class ExperimentMeta(BaseModel):

    id: str = Field(default_factory=str)
    plate: int
    cross_date: date = Field(..., alias="CrossDate")

    @model_validator(mode="after")
    def set_id(self) -> "ExperimentMeta":
        if not self.id:
            cross_date = self.cross_date.strftime("%Y")
            self.id = f"{cross_date}_{self.plate:02d}"
        return self


class PlateTimestep(BaseModel):

    experiment_id: str
    prince_position: int
    raw_img_path: Path
    img_count: int
    timestamp: datetime


class Archive(BaseModel):

    path: Path
    hash: str


class ArchivedPlateTimestep(BaseModel):

    plate_timestep: PlateTimestep
    archive: Archive
