from abc import ABC, abstractmethod
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import Select

from prince_archiver.utils import now
from prince_archiver.domain.models import DataArchiveEntry, ImagingEvent
from prince_archiver.models import Timestep
from prince_archiver.models import v2 as data_models
from prince_archiver.models.read import Export


class AbstractReadRepo(ABC):
    """
    Repository to be used with read models.
    """

    @abstractmethod
    async def get_exports(
        self, 
        start: datetime, 
        end: datetime | None = None,
    ) -> list[Export]: ...


class ReadRepo(AbstractReadRepo):
    """
    Concrete read repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_exports(
        self,
        start: datetime,
        end: datetime | None = None,
    ) -> list[Export]:
        query_params = [
            Export.uploaded_at > start,
            Export.uploaded_at < (end or now()),
        ]

        result = await self.session.stream_scalars(
            select(Export).where(*query_params),
        )
        return [item async for item in result]


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


class AbstractTimestepRepo(ABC):
    @abstractmethod
    def add(self, timestep: Timestep) -> None: ...

    @abstractmethod
    async def get(self, id: UUID) -> Timestep | None: ...

    @abstractmethod
    async def get_by_date(self, date_: date) -> list[Timestep]: ...


class TimestepRepo(AbstractTimestepRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, timestamp: Timestep) -> None:
        self.session.add(timestamp)

    async def get(self, id: UUID) -> Timestep | None:
        return await self.session.scalar(
            self._base_query().where(Timestep.timestep_id == id),
        )

    async def get_by_date(self, date_: date) -> list[Timestep]:
        result = await self.session.scalars(
            self._base_query().where(func.date(Timestep.timestamp) == date_),
        )
        return list(result.all())

    @staticmethod
    def _base_query() -> Select[tuple[Timestep]]:
        return select(Timestep).options(
            joinedload(Timestep.data_archive_entry),
            joinedload(Timestep.object_store_entry),
        )
