import logging
import os
from datetime import date, timedelta
from typing import Optional
from uuid import UUID, uuid4

from arq import cron
from arq.connections import RedisSettings
from pydantic_settings import BaseSettings, SettingsConfigDict
from zoneinfo import ZoneInfo

from surf_archiver.definitions import Mode
from surf_archiver.log import configure_remote_logging

from .client import ArchiveClientFactory

LOGGER = logging.getLogger(__name__)


class Settings(BaseSettings):
    USERNAME: str
    PASSWORD: str
    HOST: str = "archive.surfsara.nl"

    ARCHIVE_TRANSITION_DAYS: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class CronArchiver:
    def __init__(self, mode: Mode):
        self.mode = mode

    async def run(
        self,
        ctx: dict,
        *,
        _date: Optional[date] = None,
        _job_id: Optional[UUID] = None,
    ):
        job_id = _job_id or uuid4()

        settings: Settings = ctx["settings"]
        client_factory: ArchiveClientFactory = ctx["client_factory"]

        delta = timedelta(days=settings.ARCHIVE_TRANSITION_DAYS)
        archive_files_from = _date or date.today() - delta

        LOGGER.info("[%s] Initiating archiving for %s", job_id, archive_files_from)

        async with client_factory.get_managed_client() as client:
            await client.archive(archive_files_from, job_id=job_id, mode=self.mode)


async def startup(ctx: dict):
    configure_remote_logging()

    settings = Settings()

    ctx["settings"] = settings
    ctx["client_factory"] = ArchiveClientFactory(
        settings.USERNAME,
        settings.PASSWORD,
        settings.HOST,
    )


class WorkerSettings:
    queue_name = "arq:queue-surf-archiver-remote"

    cron_jobs = [
        cron(
            CronArchiver(Mode.STITCH).run,
            name="archive-images",
            hour={3},
            minute={0},
            timeout=timedelta(minutes=2),
        ),
        cron(
            CronArchiver(Mode.VIDEO).run,
            name="archive-videos",
            hour={4},
            minute={0},
            timeout=timedelta(minutes=2),
        ),
    ]

    on_startup = startup

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
