from enum import StrEnum, auto
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, HttpUrl, TypeAdapter

DataT = TypeVar("DataT")


class Params(BaseModel):
    limit: int = 99


class PaginatedResponse(BaseModel, Generic[DataT]):
    count: int
    data: list[DataT]


class EventType(StrEnum):
    STITCH = auto()


class ExportParams(Params):
    event_type: EventType = EventType.STITCH
    start: AwareDatetime
    end: AwareDatetime


class ExportModel(BaseModel):
    ref_id: UUID
    experiment_id: str
    timestamp: AwareDatetime
    type: EventType
    url: HttpUrl
    uploaded_at: AwareDatetime


ExportList = TypeAdapter(list[ExportModel])


class ArchiveParams(Params):
    experiment_id: str


class BaseArchiveModel(BaseModel):
    id: UUID
    path: str
    experiment_id: str
    created_at: AwareDatetime


class ArchiveSummaryModel(BaseArchiveModel):
    url: str


class ArchiveMember(BaseModel):
    member_key: str
    ref_id: UUID
    timestamp: AwareDatetime
    checksum: str | None
    size: int | None


class ArchiveModel(BaseArchiveModel):
    members: list[ArchiveMember]


ArchivesList = TypeAdapter(list[ArchiveModel])
