from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


class TimestempRepo(AbstractTimestepRepo):

    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, timestamp: Timestep) -> None:
        self.session.add(timestamp)


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

    timestamps: TimestempRepo

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    async def __aenter__(self) -> "UnitOfWork":
        self.session = await self.session_maker().__aenter__()
        self.timestamps = TimestempRepo(self.session)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await super().__aexit__(exc_type, exc_value, exc_traceback)
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
