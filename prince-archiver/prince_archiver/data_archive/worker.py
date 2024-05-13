import logging
import os
from datetime import date, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.logging import configure_logging

from .archiver import AbstractArchiver, Settings, SurfArchiver

LOGGER = logging.getLogger(__name__)


async def run_archiving(ctx: dict, archive_date: date | None = None):
    archive_date = archive_date or date.today() - timedelta(days=3)
    LOGGER.info("Initiating archiving %s", archive_date)

    archiver: AbstractArchiver = ctx["archiver"]

    await archiver.archive(archive_date)


async def startup(ctx: dict):
    configure_logging()

    settings = ArchiveWorkerSettings()

    ctx["archiver"] = SurfArchiver(
        settings=Settings(
            username=settings.SURF_USERNAME,
            password=settings.SURF_PASSWORD,
            host=settings.DATA_ARCHIVE_HOST,
        ),
    )

    ctx["sessionmaker"] = get_session_maker(str(settings.POSTGRES_DSN))


async def on_job_start(ctx: dict):
    session_maker: async_sessionmaker[AsyncSession] = ctx["sessionmaker"]
    ctx["uow"] = UnitOfWork(session_maker)


class WorkerSettings:

    cron_jobs = [
        cron(run_archiving, hour={2}, timeout=timedelta(hours=2)),
    ]

    on_startup = startup
    on_job_start = on_job_start

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
