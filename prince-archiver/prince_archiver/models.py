from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP, Uuid

from .utils import now


class Base(DeclarativeBase):

    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)

    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),
    }


class ObjectStoreEntry(Base):

    __tablename__ = "object_store_entry"

    id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), default=uuid4, primary_key=True
    )
    timestep_id: Mapped[int] = mapped_column(ForeignKey("prince_timestep.timestep_id"))

    key: Mapped[str]
    bucket: Mapped[str]
    expires_at: Mapped[datetime]


class DataArchiveEntry(Base):

    __tablename__ = "data_archive_entry"

    id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        default=uuid4,
        primary_key=True,
    )
    timestep_id: Mapped[int] = mapped_column(ForeignKey("prince_timestep.timestep_id"))

    job_id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False))
    file: Mapped[str]
    archive_path: Mapped[str]


class Timestep(Base):

    __tablename__ = "prince_timestep"

    timestep_id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False), primary_key=True)
    experiment_id: Mapped[str]

    position: Mapped[int]
    img_count: Mapped[int]
    timestamp: Mapped[datetime]

    local_dir: Mapped[str | None]

    object_store_entry: Mapped[ObjectStoreEntry | None] = relationship()
    data_archive_entry: Mapped[DataArchiveEntry | None] = relationship()
