from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from prince_archiver.definitions import EventType

from .value_objects import Checksum


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
class DataArchiveEntry:
    id: UUID
    type: EventType
    experiment_id: str
    path: str


@dataclass
class DataArchiveMember:
    id: UUID
    data_archive_entry_id: UUID
    member_key: str
    job_id: UUID | None = None


class ImagingEvent:
    def __init__(
        self,
        id: UUID,
        ref_id: UUID,
        type: EventType,
        experiment_id: str,
        local_path: str,
        timestamp: datetime,
        *,
        event_archive: EventArchive | None = None,
        object_store_entry: ObjectStoreEntry | None = None,
        data_archive_member: DataArchiveMember | None = None,
    ):
        self.id = id
        self.ref_id = ref_id
        self.type = type

        self.local_path = local_path
        self.timestamp = timestamp
        self.experiment_id = experiment_id

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

    @classmethod
    def factory(
        cls,
        ref_id: UUID,
        type: EventType,
        experiment_id: str,
        local_path: str,
        timestamp: datetime,
        *,
        _id: UUID | None = None,
    ):
        return cls(
            _id or uuid4(),
            ref_id,
            type,
            experiment_id,
            local_path,
            timestamp,
        )
