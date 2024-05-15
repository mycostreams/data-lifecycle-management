import logging
import os
from contextlib import AsyncExitStack
from datetime import date, timedelta
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings

from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.file import managed_file_system
from prince_archiver.logging import configure_logging
from prince_archiver.messagebus import MessageBus, MessagebusFactoryT

from .archiver import AbstractArchiver, Settings, SurfArchiver
from .dto import DeleteExpiredUploads, UpdateArchiveEntries
from .handlers import DeletedExpiredUploadsHandler, update_data_archive_entries

LOGGER = logging.getLogger(__name__)


async def run_archiving(ctx: dict, *, archive_date: date | None = None):

    archive_date = archive_date or date.today() - timedelta(days=3)
    archiver: AbstractArchiver | None = ctx["archiver"]

    if archiver:
        LOGGER.info("Initiating archiving %s", archive_date)
        await archiver.archive(archive_date)
    else:
        LOGGER.info("No archiver configured")


async def delete_expired_uploads(ctx: dict, *, date_: date | None = None):
    settings: ArchiveWorkerSettings = ctx["settings"]
    messagebus: MessageBus = ctx["messagebus"]

    job_id: UUID = ctx["job_id"]
    uploaded_on = (date_ or date.today()) - timedelta(days=settings.UPLOAD_EXPIRY_DAYS)

    LOGGER.info("Deleting uploads for %s", date_)

    await messagebus.handle(
        message=DeleteExpiredUploads(job_id=job_id, uploaded_on=uploaded_on),
    )


async def startup(ctx: dict):
    configure_logging()

    exit_stack = await AsyncExitStack().__aenter__()
    settings = ArchiveWorkerSettings()

    s3 = await exit_stack.enter_async_context(managed_file_system(settings))
    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    def _messagebus_factory():
        MessageBus(
            handlers={
                UpdateArchiveEntries: [update_data_archive_entries],
                DeleteExpiredUploads: [DeletedExpiredUploadsHandler(s3=s3)],
            },
            uow=UnitOfWork(sessionmaker),
        )

    ctx["exit_stack"] = exit_stack
    ctx["messagebus_factory"] = _messagebus_factory
    ctx["settings"] = settings

    if settings.SURF_USERNAME and settings.SURF_PASSWORD:
        ctx["archiver"] = SurfArchiver(
            settings=Settings(
                username=settings.SURF_USERNAME,
                password=settings.SURF_PASSWORD,
                host=settings.DATA_ARCHIVE_HOST,
            ),
        )


async def on_job_start(ctx: dict):
    messagebus_factory: MessagebusFactoryT = ctx["messagebus_factory"]
    ctx["messagebus"] = messagebus_factory()


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:

    cron_jobs = [
        cron(run_archiving, hour={2}, timeout=timedelta(hours=2)),
        cron(delete_expired_uploads, hour={3}, timeout=timedelta(hours=1)),
    ]

    on_startup = startup
    on_shutdown = shutdown
    on_job_start = on_job_start

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
