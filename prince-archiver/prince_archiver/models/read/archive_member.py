from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from prince_archiver.definitions import EventType
from prince_archiver.models.write import (
    ArchiveChecksum,
    DataArchiveMember,
    EventArchive,
    ImagingEvent,
    ObjectStoreEntry,
)

from .utils import ReadBase


class ArchiveMember(ReadBase):
    __table__ = (
        select(
            DataArchiveMember.id,
            DataArchiveMember.data_archive_entry_id,
            DataArchiveMember.member_key,
            ImagingEvent.ref_id,
            ImagingEvent.timestamp,
            ImagingEvent.type,
            EventArchive.size,
            ArchiveChecksum.hex.label("checksum"),
        )
        .join_from(DataArchiveMember, ObjectStoreEntry)
        .join_from(ObjectStoreEntry, ImagingEvent)
        .outerjoin_from(ImagingEvent, EventArchive)
        .outerjoin_from(EventArchive, ArchiveChecksum)
        .subquery()
    )

    id: Mapped[UUID]
    data_archive_entry_id: Mapped[UUID]
    member_key: Mapped[str]
    timestamp: Mapped[datetime]
    ref_id: Mapped[UUID]
    checksum: Mapped[str]
    size: Mapped[int]
    type: Mapped[EventType]
