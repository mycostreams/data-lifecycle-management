import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Any, AsyncGenerator
from uuid import UUID, uuid4

import asyncssh

LOGGER = logging.getLogger(__name__)


@dataclass
class Settings:
    username: str
    password: str
    host: str = "archive.surfsara.nl"
    timeout: int = 3600


class AbstractArchiver(ABC):

    @abstractmethod
    async def archive(self, date_: date, job_id: UUID | None = None): ...


class SurfArchiver(AbstractArchiver):

    COMMAND = "nohup surf-archiver {date} {job_id} > /dev/null 2>&1 &"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def archive(self, date_: date, job_id: UUID | None = None):
        job_id = job_id or uuid4()

        LOGGER.info("[%s] Archiving %s", job_id, date_)

        cmd = self._build_command(date=date_.isoformat(), job_id=job_id)
        async with self._managed_conn() as conn:
            await conn.run(cmd, check=True, timeout=self.settings.timeout)

        LOGGER.info("[%s] Archiving request sent", job_id)

    @asynccontextmanager
    async def _managed_conn(self) -> AsyncGenerator[asyncssh.SSHClientConnection, None]:
        managed_conn = asyncssh.connect(
            username=self.settings.username,
            password=self.settings.password,
            host=self.settings.host,
        )
        async with managed_conn as conn:
            yield conn

    def _build_command(self, **kwargs: Any) -> str:
        return self.COMMAND.format(**kwargs)
