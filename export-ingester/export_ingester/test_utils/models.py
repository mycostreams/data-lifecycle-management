from datetime import timedelta

from pydantic import AwareDatetime, BaseModel, Field, PositiveInt

from export_ingester.api_client.models import EventType
from export_ingester.utils import now


class PaginationParams(BaseModel):
    limit: PositiveInt = Field(250, le=250)
    offset: int = Field(0, ge=0)


class ArchivesFilterParams(PaginationParams):
    experiment_id: str


class ExportsFilterParams(PaginationParams):
    event_type: EventType = EventType.STITCH
    end: AwareDatetime = Field(default_factory=now)
    start: AwareDatetime = Field(default_factory=lambda: now() - timedelta(hours=24))
