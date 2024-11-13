from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Enum, Uuid

from prince_archiver.definitions import Algorithm, EventType, System
from prince_archiver.utils import now

from .types import PathType

uuid_pk = Annotated[
    UUID,
    mapped_column(Uuid(native_uuid=False), default=uuid4, primary_key=True),
]


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)

    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),
        Path: PathType,
    }


class DataArchiveEntry(Base):
    __tablename__ = "data_archive_entries"

    id: Mapped[uuid_pk]
    job_id: Mapped[UUID | None] = mapped_column(Uuid(native_uuid=False), default=None)
    path: Mapped[str]


class DataArchiveMember(Base):
    __tablename__ = "data_archive_members"

    id: Mapped[uuid_pk]
    member_key: Mapped[str]

    src_key: Mapped[str] = mapped_column(
        ForeignKey("object_store_entries.key"),
    )
    data_archive_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_archive_entries.id"),
    )


class ObjectStoreEntry(Base):
    __tablename__ = "object_store_entries"
    __table_args__ = (UniqueConstraint("key"),)

    id: Mapped[uuid_pk]
    key: Mapped[str]
    uploaded_at: Mapped[datetime]

    imaging_event_id: Mapped[UUID] = mapped_column(
        ForeignKey("imaging_events.id"),
    )


class ArchiveChecksum(Base):
    __tablename__ = "archive_checksums"

    id: Mapped[uuid_pk]
    hex: Mapped[str]
    algorithm: Mapped[Algorithm] = mapped_column(
        Enum(Algorithm, native_enum=False),
    )

    event_archive_id: Mapped[UUID] = mapped_column(
        ForeignKey("event_archives.id"),
    )


class SrcDirInfo(Base):
    __tablename__ = "src_dir_info"

    id: Mapped[uuid_pk]
    local_path: Mapped[Path]
    img_count: Mapped[int]

    imaging_event_id: Mapped[UUID] = mapped_column(
        ForeignKey("imaging_events.id"),
    )


class EventArchive(Base):
    __tablename__ = "event_archives"

    id: Mapped[uuid_pk]
    size: Mapped[int]

    imaging_event_id: Mapped[UUID] = mapped_column(
        ForeignKey("imaging_events.id"),
    )


class ImagingEvent(Base):
    __tablename__ = "imaging_events"

    id: Mapped[uuid_pk]
    ref_id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False))
    type: Mapped[EventType] = mapped_column(
        Enum(EventType, native_enum=False),
    )
    experiment_id: Mapped[str]
    timestamp: Mapped[datetime]

    raw_metadata: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'"),
    )

    # TODO: remove these if not needed.
    system: Mapped[System | None] = mapped_column(
        Enum(System, native_enum=False),
        nullable=True,
    )
    system_position: Mapped[int | None]
