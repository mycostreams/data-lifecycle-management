from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

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
        .join(ImagingEvent)
        .subquery()
    )
