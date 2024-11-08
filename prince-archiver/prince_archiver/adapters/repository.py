from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from prince_archiver.domain.models import DataArchiveEntry, ImagingEvent
from prince_archiver.models import write as data_models


class AbstractDataArchiveEntryRepo(ABC):
    @abstractmethod
    def add(self, data_archive_entry: DataArchiveEntry) -> None: ...

    @abstractmethod
    async def get_by_path(self, path: str) -> DataArchiveEntry | None: ...


class DataArchiveEntryRepo(AbstractDataArchiveEntryRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, data_archive_entry: DataArchiveEntry) -> None:
        self.session.add(data_archive_entry)

    async def get_by_path(self, path: str) -> DataArchiveEntry | None:
        return await self.session.scalar(
            self._base_query().where(data_models.DataArchiveEntry.path == path)
        )

    @staticmethod
    def _base_query() -> Select[tuple[DataArchiveEntry]]:
        return select(DataArchiveEntry).options(selectinload("*"))


class AbstractImagingEventRepo(ABC):
    @abstractmethod
    def add(self, image_event: ImagingEvent) -> None: ...

    @abstractmethod
    async def get_by_ref_id(self, event_id: UUID) -> ImagingEvent | None: ...

    @abstractmethod
    async def get_by_ref_date(self, date: date) -> list[ImagingEvent]: ...


class ImagingEventRepo(AbstractImagingEventRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, image_event: ImagingEvent) -> None:
        self.session.add(image_event)

    async def get_by_ref_id(self, event_id: UUID) -> ImagingEvent | None:
        return await self.session.scalar(
            self._base_query().where(
                data_models.ImagingEvent.ref_id == event_id,
            ),
        )

    async def get_by_ref_date(self, date_: date) -> list[ImagingEvent]:
        result = await self.session.scalars(
            self._base_query().where(
                func.date(data_models.ImagingEvent.timestamp) == date_,
            ),
        )
        return list(result.all())

    @staticmethod
    def _base_query() -> Select[tuple[ImagingEvent]]:
        return select(ImagingEvent).options(selectinload("*"))
