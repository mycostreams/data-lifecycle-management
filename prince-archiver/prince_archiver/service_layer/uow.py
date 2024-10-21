from abc import ABC, abstractmethod
from typing import Generator

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from prince_archiver.adapters.repository import (
    AbstractDataArchiveEntryRepo,
    AbstractImagingEventRepo,
    DataArchiveEntryRepo,
    ImagingEventRepo,
)


def get_session_maker(url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url)
    return async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


class AbstractUnitOfWork(ABC):
    messages: list[BaseModel]

    data_archive: AbstractDataArchiveEntryRepo
    imaging_events: AbstractImagingEventRepo

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await self.rollback()

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    def add_message(self, message: BaseModel): ...

    @abstractmethod
    def collect_messages(self) -> Generator[BaseModel, None, None]: ...


class UnitOfWork(AbstractUnitOfWork):
    session: AsyncSession

    data_archive: DataArchiveEntryRepo
    imaging_events: ImagingEventRepo

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker
        self.messages = []

    async def __aenter__(self) -> "UnitOfWork":
        self.session = await self.session_maker().__aenter__()

        # Initialize repos
        self.data_archive = DataArchiveEntryRepo(self.session)
        self.imaging_events = ImagingEventRepo(self.session)

        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await super().__aexit__(exc_type, exc_value, exc_traceback)
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    def add_message(self, message: BaseModel):
        self.messages.append(message)

    def collect_messages(self) -> Generator[BaseModel, None, None]:
        while self.messages:
            yield self.messages.pop(0)
