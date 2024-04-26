import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import asyncssh
from pydantic import BaseModel, TypeAdapter

LOGGER = logging.getLogger(__name__)


@dataclass
class Settings:
    username: str
    password: str
    host: str = "archive.surfsara.nl"
    timeout: int = 3600


@dataclass
class ArchiveEntry:

    source_key: str
    file: str


@dataclass
class Archive:

    path: str
    entries: list[ArchiveEntry]


class SurfArchiverSchema(BaseModel):

    path: str
    src_keys: list[str]


class AbstractArchiver(ABC):

    @abstractmethod
    async def archive(self, date_: date) -> list[Archive]: ...


class SurfArchiver(AbstractArchiver):

    # COMMAND = "surf-archiver archive {date}"
    COMMAND = "surf-archiver now"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def archive(self, date_: date) -> list[Archive]:
        cmd = self._build_command(date=date_.isoformat())
        async with self._managed_conn() as conn:
            raw_data = await conn.run(cmd, check=True, timeout=self.settings.timeout)

        archives: list[Archive] = []

        type_adapter = TypeAdapter(list[SurfArchiverSchema])
        parsed_data = type_adapter.validate_json(raw_data)
        for item in parsed_data:
            entries = []
            for path in map(Path, item.src_keys):
                entries.append(
                    ArchiveEntry(
                        file=path.name,
                        source_key=str(Path(*path.parts[1:])),
                    ),
                )
            archives.append(Archive(path=item.path, entries=entries))
        return archives

    @asynccontextmanager
    async def _managed_conn(self):
        managed_conn = asyncssh.connect(
            username=self.settings.username,
            password=self.settings.password,
            host=self.settings.host,
        )
        async with managed_conn as conn:
            yield conn

    def _build_command(self, **kwargs: Any) -> str:
        return self.COMMAND.format(**kwargs)
