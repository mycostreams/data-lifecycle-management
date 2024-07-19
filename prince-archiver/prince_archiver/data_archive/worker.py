import logging
import os
from contextlib import AsyncExitStack
from datetime import date, timedelta

from arq import cron
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.logging import configure_logging
from prince_archiver.messagebus import MessageBus

from .archiver import AbstractArchiver, Settings, SurfArchiver

LOGGER = logging.getLogger(__name__)


async def run_archiving(ctx: dict, *, _date: date | None = None):
    job_id = ctx["internal_job_id"]
    settings: ArchiveWorkerSettings = ctx["settings"]
    archiver: AbstractArchiver | None = ctx["archiver"]

    delta = timedelta(days=settings.ARCHIVE_TRANSITION_DAYS)
    archive_files_from = _date or date.today() - delta

    if archiver:
        LOGGER.info("[%s] Initiating archiving for %s", job_id, archive_files_from)
        await archiver.archive(archive_files_from)


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up")

    exit_stack = await AsyncExitStack().__aenter__()
    settings = ArchiveWorkerSettings()

    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    def _messagebus_factory() -> MessageBus:
        return MessageBus(
            handlers={},
            uow=UnitOfWork(sessionmaker),
        )

    ctx["exit_stack"] = exit_stack
    ctx["settings"] = settings

    if settings.SURF_USERNAME and settings.SURF_PASSWORD:
        LOGGER.info("Adding archiver")
        ctx["archiver"] = SurfArchiver(
            settings=Settings(
                username=settings.SURF_USERNAME,
                password=settings.SURF_PASSWORD,
                host=settings.DATA_ARCHIVE_HOST,
            ),
        )

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-cron"

    cron_jobs = [
        cron(run_archiving, hour={2}, minute={0}, timeout=timedelta(minutes=2)),
    ]

    on_startup = startup
    on_shutdown = shutdown

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
