from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from prince_archiver.definitions import EventType
from prince_archiver.models.v2 import ImagingEvent, ObjectStoreEntry

from .utils import ReadBase


class Export(ReadBase):
    __table__ = (
        select(
            ImagingEvent.id,
            ImagingEvent.ref_id,
            ImagingEvent.type,
            ImagingEvent.timestamp,
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
    type: Mapped[EventType]
    key: Mapped[str]
    uploaded_at: Mapped[datetime]
