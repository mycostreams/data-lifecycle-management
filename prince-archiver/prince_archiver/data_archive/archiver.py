import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any

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
    async def archive(self, date_: date): ...


class SurfArchiver(AbstractArchiver):

    # COMMAND = "surf-archiver archive {date} --bucket_name {bucket}"
    COMMAND = "surf-archiver now"

    def __init__(self, settings: Settings, bucket: str):
        self.bucket = bucket
        self.settings = settings

    async def archive(self, date_: date):
        cmd = self._build_command(date=date_.isoformat(), bucket=self.bucket)

        managed_conn = asyncssh.connect(
            username=self.settings.username,
            password=self.settings.password,
            host=self.settings.host,
        )
        async with managed_conn as conn:
            await conn.run(cmd, check=True, timeout=self.settings.timeout)

    def _build_command(self, **kwargs: Any) -> str:
        return self.COMMAND.format(**kwargs)
