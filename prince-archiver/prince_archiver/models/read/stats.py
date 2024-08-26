from datetime import date

from sqlalchemy import Subquery, func, select
from sqlalchemy.orm import InstrumentedAttribute, Mapped

from prince_archiver.models.v2 import DataArchiveMember, ImagingEvent, ObjectStoreEntry

from .utils import ReadBase


def query_builder() -> Subquery:
    """
    Build subquery to be passed into `DailyStats` model.
    """

    def build_count_subquery(
        field: InstrumentedAttribute,
        count_label: str,
    ) -> Subquery:
        _date_field = func.date(field).label("date")
        return (
            select(_date_field, func.count(_date_field).label(count_label))
            .group_by(_date_field)
            .subquery()
        )

    event_count = build_count_subquery(ImagingEvent.timestamp, "event_count")
    upload_count = build_count_subquery(ObjectStoreEntry.uploaded_at, "export_count")
    archive_count = build_count_subquery(DataArchiveMember.created_at, "archive_count")

    t1 = (
        select(
            func.coalesce(event_count.c.date, upload_count.c.date).label("date"),
            event_count.c.event_count,
            upload_count.c.export_count,
        )
        .join_from(
            event_count,
            upload_count,
            onclause=event_count.c.date == upload_count.c.date,
            full=True,
        )
        .subquery()
    )

    return (
        select(
            func.coalesce(t1.c.date, archive_count.c.date).label("date"),
            func.coalesce(t1.c.event_count, 0).label("event_count"),
            func.coalesce(t1.c.export_count, 0).label("export_count"),
            func.coalesce(archive_count.c.archive_count, 0).label("archive_count"),
        )
        .join_from(
            t1,
            archive_count,
            onclause=t1.c.date == archive_count.c.date,
            full=True,
        )
        .subquery()
    )


class DailyStats(ReadBase):
    __table__ = query_builder()
    __mapper_args__ = {"primary_key": __table__.c.date}

    date: Mapped[date]
    event_count: Mapped[int]
    export_count: Mapped[int]
    archive_count: Mapped[int]
