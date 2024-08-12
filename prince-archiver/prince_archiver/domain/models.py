from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from prince_archiver.definitions import EventType

from .value_objects import Checksum, GridSize, Location


@dataclass
class EventArchive:
    id: UUID
    size: int
    img_count: int
    checksum: Checksum | None = None


@dataclass
class ObjectStoreEntry:
    id: UUID
    key: str
    uploaded_at: datetime


@dataclass
class DataArchiveMember:
    id: UUID
    key: str
    member_key: str
    job_id: UUID | None = None


@dataclass
class Params:
    pass


@dataclass
class StitchParams(Params):
    grid_size: GridSize


@dataclass
class VideoParams(Params):
    pass


ParamT = TypeVar("ParamT", bound=Params)


class ImagingEvent(Generic[ParamT]):
    def __init__(
        self,
        id: UUID,
        ref_id: UUID,
        type: EventType,
        experiment_id: str,
        local_path: str,
        timestamp: datetime,
        location: Location,
        *,
        event_archive: EventArchive | None = None,
        object_store_entry: ObjectStoreEntry | None = None,
        data_archive_member: DataArchiveMember | None = None,
        _params: ParamT | None = None,
    ):
        self.id = id
        self.ref_id = ref_id
        self.type = type

        self.local_path = local_path
        self.timestamp = timestamp
        self.experiment_id = experiment_id
        self.location = location

        self._params = _params
        self.event_archive = event_archive
        self.object_store_entry = object_store_entry
        self.data_archive_member = data_archive_member

    def add_event_archive(self, event_archive: EventArchive):
        if self.event_archive:
            raise ValueError("error")
        self.event_archive = event_archive

    def add_object_store_entry(self, object_store_entry: ObjectStoreEntry):
        if self.object_store_entry:
            raise ValueError("error")
        self.object_store_entry = object_store_entry

    def add_data_archive_member(self, archive_member: DataArchiveMember):
        if self.data_archive_member:
            raise ValueError("error")
        self.data_archive_member = archive_member


class ConcreteImagingEvent(ImagingEvent[ParamT]):
    TYPE: EventType
    PARAM_CLS: type[ParamT]

    @classmethod
    def factory(
        cls,
        ref_id: UUID,
        experiment_id: str,
        local_path: str,
        timestamp: datetime,
        location: Location,
        *,
        params: ParamT | None = None,
        _id: UUID | None = None,
    ):
        return cls(
            _id or uuid4(),
            ref_id,
            cls.TYPE,
            experiment_id,
            local_path,
            timestamp,
            location,
            _params=params,
        )

    @property
    def params(self):
        return self._params

    @classmethod
    def get_param_cls(cls) -> type[ParamT]:
        return cls.PARAM_CLS


class StitchEvent(ConcreteImagingEvent[StitchParams]):
    """
    Imaging event for stitch events.
    """

    TYPE = EventType.STITCH
    PARAM_CLS = StitchParams


class VideoEvent(ConcreteImagingEvent[VideoParams]):
    """
    Imaging event for video events.
    """

    TYPE = EventType.VIDEO
    PARAM_CLS = VideoParams
