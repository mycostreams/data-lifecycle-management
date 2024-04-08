"""Definition of data transfer objects."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


@dataclass(kw_only=True)
class DirectoryConfig:

    param_filename = "param.json"
    img_dir_name: str = "Img"
    final_img_name: str = "Img_r10_c15.tif"


class TimestepMeta(BaseModel):

    timestep_id: UUID = Field(default_factory=uuid4)
    plate: int
    cross_date: date
    position: int
    timestamp: datetime


class TimestepDTO(TimestepMeta):

    timestep_dir_name: str
    img_dir_name: str

    img_count: int = 150

    experiment_id: str = Field(default_factory=str)
    archive_name: str = Field(default_factory=str)

    @model_validator(mode="after")
    def set_experiment_id(self) -> "TimestepDTO":
        if not self.experiment_id:
            cross_date = self.cross_date.strftime("%Y")
            self.experiment_id = f"{cross_date}_{self.plate:02d}"
        return self

    @model_validator(mode="after")
    def set_archive_name(self) -> "TimestepDTO":
        if not self.archive_name:
            self.archive_name = self.timestamp.strftime("%Y%m%d_%H%M.tar")
        return self

    @property
    def key(self) -> str:
        return f"{self.experiment_id}/{self.archive_name}"

    @property
    def parent_archive(self) -> str:
        date_str = self.timestamp.strftime("%Y-%m-%d")
        return f"{self.experiment_id}/{date_str}.tar"
