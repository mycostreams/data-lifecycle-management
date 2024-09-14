from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from prince_archiver.definitions import EventType, System

from .exceptions import DomainException
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
class SrcDirInfo:
    staging_path: Path | None
    local_path: Path
    img_count: int
    raw_metadata: dict[str, Any]


@dataclass
class EventArchive:
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
        system: System,
        type: EventType,
        experiment_id: str,
        timestamp: datetime,
        src_dir_info: SrcDirInfo,
        *,
        event_archive: EventArchive | None = None,
        object_store_entry: ObjectStoreEntry | None = None,
    ):
        self.id = id
        self.ref_id = ref_id
        self.type = type
        self.system = system
        self.timestamp = timestamp
        self.experiment_id = experiment_id
        self.src_dir_info = src_dir_info

        self.event_archive = event_archive
        self.object_store_entry = object_store_entry

    def add_event_archive(self, event_archive: EventArchive):
        if self.event_archive:
            raise DomainException("Already associated")
        self.event_archive = event_archive

    def add_object_store_entry(self, object_store_entry: ObjectStoreEntry):
        if self.object_store_entry:
            raise DomainException("Already associated")
        self.object_store_entry = object_store_entry

    @classmethod
    def factory(
        cls,
        ref_id: UUID,
        system: System,
        type: EventType,
        experiment_id: str,
        timestamp: datetime,
        src_dir_info: SrcDirInfo,
        *,
        _id: UUID | None = None,
    ):
        return cls(
            _id or uuid4(),
            ref_id,
            system,
            type,
            experiment_id,
            timestamp,
            src_dir_info,
        )
