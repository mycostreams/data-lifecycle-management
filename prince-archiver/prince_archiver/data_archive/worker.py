import logging
import os
from contextlib import AsyncExitStack
from datetime import date, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

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


async def run_archiving(ctx: dict, *, _date: date | None = None):
    job_id = ctx["internal_job_id"]
    settings: ArchiveWorkerSettings = ctx["settings"]
    archiver: AbstractArchiver | None = ctx["archiver"]

    delta = timedelta(days=settings.ARCHIVE_TRANSITION_DAYS)
    archive_files_from = _date or date.today() - delta

    if archiver:
        LOGGER.info("[%s] Initiating archiving for %s", job_id, archive_files_from)
        await archiver.archive(archive_files_from)


async def delete_expired_uploads(ctx: dict, *, _date: date | None = None):
    job_id: UUID = ctx["internal_job_id"]
    settings: ArchiveWorkerSettings = ctx["settings"]
    messagebus: MessageBus = ctx["messagebus"]

    uploaded_on = (_date or date.today()) - timedelta(days=settings.UPLOAD_EXPIRY_DAYS)

    LOGGER.info("[%s] Deleting uploads for %s", job_id, uploaded_on)

    await messagebus.handle(
        message=DeleteExpiredUploads(
            job_id=job_id,
            uploaded_on=uploaded_on,
        ),
    )


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up")

    exit_stack = await AsyncExitStack().__aenter__()
    settings = ArchiveWorkerSettings()

    s3 = await exit_stack.enter_async_context(managed_file_system(settings))
    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    def _messagebus_factory() -> MessageBus:
        return MessageBus(
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
        LOGGER.info("Adding archiver")
        ctx["archiver"] = SurfArchiver(
            settings=Settings(
                username=settings.SURF_USERNAME,
                password=settings.SURF_PASSWORD,
                host=settings.DATA_ARCHIVE_HOST,
            ),
        )

    LOGGER.info("Start up complete")


async def job_start(ctx: dict):
    messagebus_factory: MessagebusFactoryT = ctx["messagebus_factory"]

    ctx["messagebus"] = messagebus_factory()
    ctx["internal_job_id"] = uuid4()


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:

    queue_name = "arq:queue-cron"

    cron_jobs = [
        cron(run_archiving, hour={2}, minute={0}, timeout=timedelta(minutes=2)),
        cron(delete_expired_uploads, hour={2}, minute={0}, timeout=timedelta(hours=1)),
    ]

    on_startup = startup
    on_shutdown = shutdown
    on_job_start = job_start

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
