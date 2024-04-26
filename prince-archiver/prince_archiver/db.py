from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import Select

from .models import Timestep


def get_session_maker(url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url)
    return async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


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


class AbstractUnitOfWork(ABC):

    timestamps: AbstractTimestepRepo

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await self.rollback()

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...


class UnitOfWork(AbstractUnitOfWork):

    session: AsyncSession

    timestamps: TimestepRepo

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    async def __aenter__(self) -> "UnitOfWork":
        self.session = await self.session_maker().__aenter__()
        self.timestamps = TimestepRepo(self.session)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await super().__aexit__(exc_type, exc_value, exc_traceback)
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
