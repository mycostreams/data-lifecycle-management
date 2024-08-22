from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped

from .v2 import ImagingEvent, ObjectStoreEntry


class ReadBase(DeclarativeBase):
    pass


class Export(ReadBase):
    __table__ = (
        select(
            ImagingEvent.id,
            ImagingEvent.ref_id,
            ImagingEvent.experiment_id,
            ObjectStoreEntry.key,
            ObjectStoreEntry.uploaded_at,
        )
        .join_from(ObjectStoreEntry, ImagingEvent)
        .subquery()
    )

    id: Mapped[UUID]
    ref_id: Mapped[UUID]
    experiment_id: Mapped[str]
    key: Mapped[str]
    uploaded_at: Mapped[datetime]
