from datetime import date, datetime, timedelta
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl

from prince_archiver.definitions import EventType
from prince_archiver.utils import now


class ExportFilterParams(BaseModel):
    start: AwareDatetime = Field(default_factory=lambda: now() - timedelta(hours=24))
    end: AwareDatetime = Field(default_factory=now)
    event_type: EventType = EventType.STITCH
    limit: int = Field(500, le=500)
    offset: int = Field(0, ge=0)


class DailyStatsModel(BaseModel):
    date: date
    event_count: int
    export_count: int
    archive_count: int


class ExportModel(BaseModel):
    ref_id: UUID
    experiment_id: str
    timestamp: datetime
    type: EventType
    url: HttpUrl | None = None
    uploaded_at: datetime


class ExportsModel(BaseModel):
    count: int
    data: list[ExportModel]


class BaseArchiveModel(BaseModel):
    id: UUID
    path: str
    type: EventType
    experiment_id: str
    created_at: datetime


class ArchiveSummaryModel(BaseArchiveModel):
    url: str
    member_count: int


class ArchivesModel(BaseModel):
    count: int
    data: list[ArchiveSummaryModel]


class ArchiveMemberModel(BaseModel):
    member_key: str
    ref_id: UUID
    timestamp: datetime
    checksum: str | None
    size: int | None


class ArchiveModel(BaseArchiveModel):
    members: list[ArchiveMemberModel]
