import logging
import os
from datetime import date, timedelta
from typing import Optional
from uuid import UUID, uuid4

from arq import cron
from arq.connections import RedisSettings
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from zoneinfo import ZoneInfo

from surf_archiver.log import configure_remote_logging

from .client import ArchiveClientFactory

LOGGER = logging.getLogger(__name__)


class Settings(BaseSettings):
    USERNAME: str = Field(default=...)
    PASSWORD: str = Field(default=...)
    HOST: str = "archive.surfsara.nl"

    ARCHIVE_TRANSITION_DAYS: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


async def run_archiving(
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
        await client.archive(archive_files_from, job_id=job_id)


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
        cron(run_archiving, hour={15}, minute={15, 16}, timeout=timedelta(minutes=2)),
    ]

    on_startup = startup

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
