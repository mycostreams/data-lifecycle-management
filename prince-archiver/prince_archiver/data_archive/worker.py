import logging
import os
from datetime import date, timedelta

from arq import cron
from arq.connections import RedisSettings

from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.logging import configure_logging

from .archiver import AbstractArchiver, Settings, SurfArchiver

LOGGER = logging.getLogger(__name__)


async def run_archiving(ctx: dict):
    archiver: AbstractArchiver = ctx["archiver"]
    archive_date = date.today() - timedelta(days=3)

    LOGGER.info("Initiating archiving %s", archive_date)

    await archiver.archive(archive_date)


async def startup(ctx: dict):
    configure_logging()

    settings = ArchiveWorkerSettings()

    ctx["archiver"] = SurfArchiver(
        settings=Settings(
            settings.SURF_USERNAME,
            settings.SURF_PASSWORD,
        ),
        bucket=settings.AWS_BUCKET_NAME,
    )


class WorkerSettings:

    cron_jobs = [
        cron(run_archiving, hour={2}, timeout=timedelta(hours=2)),
    ]

    on_startup = startup

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
