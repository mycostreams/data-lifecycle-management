from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Timestep(Base):

    __tablename__ = "prince_timestep"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str]
    key: Mapped[str] = mapped_column(default=lambda: uuid4().hex)
    prince_position: Mapped[int]
    img_count: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column("imaging_timestamp")

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
