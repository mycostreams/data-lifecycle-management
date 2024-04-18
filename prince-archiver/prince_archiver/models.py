from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Uuid

from .utils import now


class Base(DeclarativeBase):

    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),
    }


class Timestep(Base):

    __tablename__ = "prince_timestep"

    timestep_id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False), primary_key=True)
    experiment_id: Mapped[str]
    archive_name: Mapped[str]
    position: Mapped[int]
    img_count: Mapped[int]
    timestamp: Mapped[datetime]
    src_dir: Mapped[str]
    is_active: Mapped[bool | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)
