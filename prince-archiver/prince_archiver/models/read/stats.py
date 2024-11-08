from datetime import date

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Mapped

from prince_archiver.models.write import (
    DataArchiveMember,
    ImagingEvent,
    ObjectStoreEntry,
)

from .utils import ReadBase


def query_builder() -> Select:
    subquery = (
        select(
            ImagingEvent.id,
            func.date(ImagingEvent.timestamp).label("date"),
            case((ObjectStoreEntry.id.is_(None), 0), else_=1).label("is_exported"),
            case((DataArchiveMember.id.is_(None), 0), else_=1).label("is_archived"),
        )
        .outerjoin_from(ImagingEvent, ObjectStoreEntry)
        .outerjoin_from(ObjectStoreEntry, DataArchiveMember)
        .subquery()
    )
    return select(
        subquery.c.date,
        func.count().label("event_count"),
        func.sum(subquery.c.is_exported).label("export_count"),
        func.sum(subquery.c.is_archived).label("archive_count"),
    ).group_by(subquery.c.date)


class DailyStats(ReadBase):
    __table__ = query_builder().subquery()
    __mapper_args__ = {"primary_key": __table__.c.date}

    date: Mapped[date]
    event_count: Mapped[int]
    export_count: Mapped[int]
    archive_count: Mapped[int]
