from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    pass


class Timestep(Base):

    __tablename__ = "prince_timestep"

    timestep_id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False), primary_key=True)
    experiment_id: Mapped[str]
    archive_name: Mapped[str]
    position: Mapped[int]
    img_count: Mapped[int]
    timestamp: Mapped[datetime]

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
