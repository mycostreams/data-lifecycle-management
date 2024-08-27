from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from prince_archiver.definitions import EventType

from .value_objects import Checksum


@dataclass
class ArchiveMember:
    member_key: str
    src_key: str


class DataArchiveEntry:
    def __init__(
        self,
        id: UUID,
        path: str,
        job_id: UUID | None,
        members: list[ArchiveMember] | None = None,
    ):
        self.id = id
        self.path = path
        self.job_id = job_id
        self.members = members or []


@dataclass
class EventArchive:
    id: UUID
    size: int
    checksum: Checksum | None = None


@dataclass
class ObjectStoreEntry:
    key: str
    uploaded_at: datetime


class ImagingEvent:
    def __init__(
        self,
        id: UUID,
        ref_id: UUID,
        type: EventType,
        experiment_id: str,
        local_path: Path,
        timestamp: datetime,
        *,
        event_archive: EventArchive | None = None,
        object_store_entry: ObjectStoreEntry | None = None,
    ):
        self.id = id
        self.ref_id = ref_id
        self.type = type

        self.local_path = local_path
        self.timestamp = timestamp
        self.experiment_id = experiment_id

        self.event_archive = event_archive
        self.object_store_entry = object_store_entry

    def add_event_archive(self, event_archive: EventArchive):
        if self.event_archive:
            raise ValueError("error")
        self.event_archive = event_archive

    def add_object_store_entry(self, object_store_entry: ObjectStoreEntry):
        if self.object_store_entry:
            raise ValueError("error")
        self.object_store_entry = object_store_entry

    @classmethod
    def factory(
        cls,
        ref_id: UUID,
        type: EventType,
        experiment_id: str,
        local_path: Path,
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
