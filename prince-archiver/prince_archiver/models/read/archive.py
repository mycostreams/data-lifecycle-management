from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Mapped

from prince_archiver.definitions import EventType
from prince_archiver.models.write import (
    DataArchiveEntry,
    DataArchiveMember,
    ImagingEvent,
    ObjectStoreEntry,
)

from .utils import ReadBase


def query_builder():
    nested_query = (
        select(
            DataArchiveMember.data_archive_entry_id.label("id"),
            ImagingEvent.experiment_id,
            ImagingEvent.type,
            func.count(DataArchiveMember.data_archive_entry_id).label("member_count"),
        )
        .join_from(DataArchiveMember, ObjectStoreEntry)
        .join_from(ObjectStoreEntry, ImagingEvent)
        .group_by(
            DataArchiveMember.data_archive_entry_id,
            ImagingEvent.experiment_id,
            ImagingEvent.type,
        )
        .distinct(DataArchiveMember.data_archive_entry_id)
        .subquery()
    )

    return (
        select(
            DataArchiveEntry.id,
            DataArchiveEntry.path,
            nested_query.c.type,
            nested_query.c.experiment_id,
            nested_query.c.member_count,
            DataArchiveEntry.created_at,
        )
        .join_from(
            DataArchiveEntry,
            nested_query,
            onclause=DataArchiveEntry.id == nested_query.c.id,
        )
        .subquery()
    )


class Archive(ReadBase):
    __table__ = query_builder()

    id: Mapped[UUID]
    path: Mapped[str]
    type: Mapped[EventType]
    created_at: Mapped[datetime]
    member_count: Mapped[int]
    experiment_id: Mapped[str]
