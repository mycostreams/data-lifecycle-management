import logging
import os
from datetime import date, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.db import AbstractUnitOfWork, UnitOfWork, get_session_maker
from prince_archiver.logging import configure_logging
from prince_archiver.models import DataArchiveEntry

from .archiver import AbstractArchiver, Settings, SurfArchiver

LOGGER = logging.getLogger(__name__)


async def run_archiving(ctx: dict, archive_date: date | None = None):
    archive_date = archive_date or date.today() - timedelta(days=3)
    LOGGER.info("Initiating archiving %s", archive_date)

    archiver: AbstractArchiver = ctx["archiver"]
    uow: AbstractUnitOfWork = ctx["uow"]

    async with uow:
        archives = await archiver.archive(archive_date)

        mapping: dict[str, DataArchiveEntry] = {}
        for item in archives:
            for entry in item.entries:
                mapping[entry.source_key] = DataArchiveEntry(
                    file=entry.file,
                    archive_path=item.path,
                )

        timestamps = await uow.timestamps.get_by_date(archive_date)
        for timestep in timestamps:
            if object_store_entry := timestep.object_store_entry:
                timestep.data_archive_entry = mapping.get(object_store_entry.key)

        await uow.commit()


async def startup(ctx: dict):
    configure_logging()

    settings = ArchiveWorkerSettings()

    ctx["archiver"] = SurfArchiver(
        settings=Settings(
            settings.SURF_USERNAME,
            settings.SURF_PASSWORD,
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
