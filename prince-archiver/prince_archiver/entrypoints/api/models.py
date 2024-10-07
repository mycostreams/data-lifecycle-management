from datetime import datetime, timedelta
from typing import Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl, model_validator

from prince_archiver.definitions import EventType
from prince_archiver.utils import now


class FilterParams(BaseModel):
    start: AwareDatetime = Field(default_factory=lambda: now() - timedelta(hours=24))
    end: AwareDatetime = Field(default_factory=now)
    event_type: EventType = EventType.STITCH

    @model_validator(mode="after")
    def validate_time_range(self) -> Self:
        max_delta = timedelta(hours=36)
        if (self.end - self.start) > max_delta:
            raise ValueError(f"Time range must be less than {max_delta}")
        return self


class ExportModel(BaseModel):
    id: UUID
    ref_id: UUID
    experiment_id: str
    type: EventType
    url: HttpUrl | None = None
    uploaded_at: datetime
