from datetime import datetime, timedelta
from uuid import UUID
from typing import Self

from pydantic import AwareDatetime, BaseModel, HttpUrl, model_validator, Field


from prince_archiver.definitions import EventType
from prince_archiver.utils import now


class FilterParams(BaseModel):
    start: AwareDatetime = Field(default_factory=lambda: now() - timedelta(hours=24))
    end: AwareDatetime = Field(default_factory=now)
    event_type: EventType = EventType.STITCH

    @model_validator(mode="after")
    def validate_time_range(self) -> Self:
        if (self.end - self.start) > timedelta(hours=36):
            raise ValueError("")
        return self


class ExportModel(BaseModel):
    id: UUID
    ref_id: UUID
    experiment_id: str
    type: EventType
    url: HttpUrl | None = None
    uploaded_at: datetime
