from abc import ABC, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Timestep


def get_session_maker(url: str) -> sessionmaker[Session]:
    engine = create_engine(url)
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


class AbstractTimestepRepo(ABC):

    @abstractmethod
    def add(self, timestep: Timestep) -> None: ...


class TimestempRepo(AbstractTimestepRepo):

    def __init__(self, session: Session):
        self.session = session

    def add(self, timestamp: Timestep) -> None:
        self.session.add(timestamp)


class AbstractUnitOfWork(ABC):

    timestamps: AbstractTimestepRepo

    @abstractmethod
    def __enter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.rollback()

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...


class UnitOfWork(AbstractUnitOfWork):

    session: Session

    timestamps: TimestempRepo

    def __init__(self, session_maker: sessionmaker[Session]):
        self.session_maker = session_maker

    def __enter__(self) -> "UnitOfWork":
        self.session = self.session_maker()
        self.timestamps = TimestempRepo(self.session)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
