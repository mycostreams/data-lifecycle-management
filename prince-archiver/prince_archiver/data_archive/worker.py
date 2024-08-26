import logging
import os
from contextlib import AsyncExitStack
from datetime import date, timedelta
from functools import partial
from typing import Callable
from uuid import UUID, uuid4

from arq import cron
from arq.connections import RedisSettings
from httpx import AsyncClient
from zoneinfo import ZoneInfo

from prince_archiver.adapters.archiver import AbstractArchiver, Settings, SurfArchiver
from prince_archiver.adapters.subscriber import ManagedSubscriber
from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.file import managed_file_system
from prince_archiver.logging import configure_logging
from prince_archiver.service_layer.external_dto import UpdateArchiveEntries
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .handlers import (
    SubscriberMessageHandler,
    add_data_archive_entries,
)
from .reporter import Messenger, Reporter

LOGGER = logging.getLogger(__name__)


async def run_archiving(
    ctx: dict,
    *,
    _date: date | None = None,
    _job_id: UUID | None = None,
):
    job_id = _job_id or uuid4()
    settings: ArchiveWorkerSettings = ctx["settings"]
    archiver: AbstractArchiver | None = ctx["archiver"]

    delta = timedelta(days=settings.ARCHIVE_TRANSITION_DAYS)
    archive_files_from = _date or date.today() - delta

    if archiver:
        LOGGER.info("[%s] Initiating archiving for %s", job_id, archive_files_from)
        await archiver.archive(archive_files_from)


async def run_reporting(ctx: dict, *, _date: date | None = None):
    settings: ArchiveWorkerSettings = ctx["settings"]
    uow_factory: Callable[[], UnitOfWork] = ctx["uow_factory"]

    reporter: Reporter = ctx["reporter"]
    report_date = _date or date.today() - timedelta(days=1)

    target = f"{settings.AWS_BUCKET_NAME}/daily-reports/{report_date.isoformat()}.json"

    LOGGER.info("Generating daily report for %s", report_date.isoformat())
    await reporter.generate_report(uow_factory(), date=report_date, target=target)


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up")

    exit_stack = await AsyncExitStack().__aenter__()
    settings = ArchiveWorkerSettings()

    uow_factory = partial(
        UnitOfWork,
        get_session_maker(str(settings.POSTGRES_DSN)),
    )

    def _messagebus_factory() -> MessageBus:
        return MessageBus(
            handlers={UpdateArchiveEntries: [add_data_archive_entries]},
            uow=uow_factory(),
        )

    ctx["exit_stack"] = exit_stack
    ctx["settings"] = settings
    ctx["uow_factory"] = uow_factory

    # Configure archive subscriber
    subscriber = ManagedSubscriber(
        connection_url=settings.RABBITMQ_DSN,
        message_handler=SubscriberMessageHandler(_messagebus_factory),
    )
    await exit_stack.enter_async_context(subscriber)

    # Configure archiver
    if settings.SURF_USERNAME and settings.SURF_PASSWORD:
        LOGGER.info("Adding archiver")
        ctx["archiver"] = SurfArchiver(
            settings=Settings(
                username=settings.SURF_USERNAME,
                password=settings.SURF_PASSWORD,
                host=settings.DATA_ARCHIVE_HOST,
            ),
        )

    # Configure reporter
    messenger: Messenger | None = None
    if settings.WEBHOOK_URL:
        client = await exit_stack.enter_async_context(AsyncClient())
        messenger = Messenger(client, str(settings.WEBHOOK_URL))
    s3 = await exit_stack.enter_async_context(managed_file_system(settings))

    ctx["reporter"] = Reporter(s3, messenger=messenger)

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-cron"

    cron_jobs = [
        cron(run_reporting, hour={7}, minute={0}),
        cron(run_archiving, hour={2}, minute={0}, timeout=timedelta(minutes=2)),
    ]

    on_startup = startup
    on_shutdown = shutdown

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
