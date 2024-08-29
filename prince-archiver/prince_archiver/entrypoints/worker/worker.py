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
from prince_archiver.adapters.messenger import Message, Messenger
from prince_archiver.adapters.subscriber import ManagedSubscriber
from prince_archiver.config import ArchiveWorkerSettings
from prince_archiver.logging import configure_logging
from prince_archiver.service_layer.handlers.archive import add_data_archive_entry
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import AddDataArchiveEntry
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .external import SubscriberMessageHandler

LOGGER = logging.getLogger(__name__)


async def run_archiving(
    ctx: dict,
    *,
    _date: date | None = None,
    _job_id: UUID | None = None,
):
    job_id = _job_id or uuid4()
    settings: ArchiveWorkerSettings = ctx["settings"]
    archiver: AbstractArchiver | None = ctx.get("archiver", None)

    delta = timedelta(days=settings.ARCHIVE_TRANSITION_DAYS)
    archive_files_from = _date or date.today() - delta

    if archiver:
        LOGGER.info("[%s] Initiating archiving for %s", job_id, archive_files_from)
        await archiver.archive(archive_files_from)


async def run_reporting(ctx: dict, *, _date: date | None = None):
    messenger: Messenger | None = ctx.get("messenger", None)
    uow_factory: Callable[[], UnitOfWork] = ctx["uow_factory"]

    report_date = _date or date.today() - timedelta(days=1)

    if messenger:
        async with uow_factory() as uow:
            stats = filter(
                lambda stats: stats.date == report_date,
                await uow.read.get_daily_stats(start=report_date),
            )
            if daily_stats := next(stats, None):
                await messenger.publish(Message.DAILY_STATS, **daily_stats.__dict__)


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up")

    exit_stack = await AsyncExitStack().__aenter__()
    settings = ArchiveWorkerSettings()

    uow_factory = partial(
        UnitOfWork,
        get_session_maker(str(settings.POSTGRES_DSN)),
    )

    messagebus_factory = MessageBus.factory(
        handlers={AddDataArchiveEntry: [add_data_archive_entry]},
        uow=uow_factory,
    )

    ctx["exit_stack"] = exit_stack
    ctx["settings"] = settings
    ctx["uow_factory"] = uow_factory

    # Configure archive subscriber
    subscriber = ManagedSubscriber(
        connection_url=settings.RABBITMQ_DSN,
        message_handler=SubscriberMessageHandler(messagebus_factory),
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

    # Configure messenger
    if settings.WEBHOOK_URL:
        LOGGER.info("Adding messenger")
        client = await exit_stack.enter_async_context(AsyncClient())
        ctx["messenger"] = Messenger(client, str(settings.WEBHOOK_URL))

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
