from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from .definitions import Mode
from .utils import DateT

ConfigT = TypeVar("ConfigT", bound="AbstractConfig")


@dataclass
class AbstractConfig:
    pass


@dataclass
class ArchiveEntry:
    path: str
    src_keys: list[str]


@dataclass
class ArchiveParams:
    mode: Mode
    date: DateT
    job_id: UUID = field(default_factory=uuid4)


class AbstractArchiver(ABC):
    @abstractmethod
    async def archive(
        self,
        archive_params: ArchiveParams,
    ) -> list[ArchiveEntry]: ...


class AbstractManagedArchiver(Generic[ConfigT], ABC):
    def __init__(self, config: ConfigT):
        self.config = config

    @abstractmethod
    async def __aenter__(self) -> AbstractArchiver: ...

    @abstractmethod
    async def __aexit__(self, *args) -> None: ...
