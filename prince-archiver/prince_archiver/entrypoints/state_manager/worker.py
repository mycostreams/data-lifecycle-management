import logging
import os
from contextlib import AsyncExitStack
from datetime import timedelta
from functools import partial
from typing import Any

from arq import ArqRedis, cron
from arq.connections import RedisSettings
from httpx import AsyncClient
from zoneinfo import ZoneInfo

from prince_archiver.adapters.archiver import Settings as ArchiverSettings
from prince_archiver.adapters.archiver import SurfArchiver
from prince_archiver.adapters.messenger import Messenger
from prince_archiver.adapters.streams import Stream
from prince_archiver.adapters.subscriber import ManagedSubscriber
from prince_archiver.log import configure_logging
from prince_archiver.models import init_mappers
from prince_archiver.service_layer.handlers.archive import add_data_archive_entry
from prince_archiver.service_layer.handlers.export import persist_imaging_event_export
from prince_archiver.service_layer.handlers.ingest import import_imaging_event
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import (
    AddDataArchiveEntry,
    ExportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.streams import Streams
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .external import SubscriberMessageHandler
from .functions import State, run_archiving, run_persist_export, run_reporting
from .settings import Settings
from .stream import managed_stream_ingester

LOGGER = logging.getLogger(__name__)


async def startup(ctx: dict):
    configure_logging()
    init_mappers()

    LOGGER.info("Starting up")

    exit_stack = await AsyncExitStack().__aenter__()

    settings = Settings()

    uow_factory = partial(
        UnitOfWork,
        get_session_maker(str(settings.POSTGRES_DSN)),
    )

    messagebus_factory = MessageBus.factory(
        handlers={
            ImportImagingEvent: [import_imaging_event],
            ExportedImagingEvent: [persist_imaging_event_export],
            AddDataArchiveEntry: [add_data_archive_entry],
        },
        uow=uow_factory,
    )

    redis: ArqRedis = ctx["redis"]
    stream = Stream(redis=redis, stream=Streams.new_imaging_event)

    # Configure optional state
    optional_state: dict[str, Any] = {}

    if settings.SURF_USERNAME and settings.SURF_PASSWORD:
        LOGGER.info("Adding archiver")
        optional_state["archiver"] = SurfArchiver(
            settings=ArchiverSettings(
                username=settings.SURF_USERNAME,
                password=settings.SURF_PASSWORD,
                host=settings.DATA_ARCHIVE_HOST,
            ),
        )

    # Configure messenger
    if settings.WEBHOOK_URL:
        LOGGER.info("Adding messenger")
        client = await exit_stack.enter_async_context(AsyncClient())
        optional_state["messenger"] = Messenger(client, str(settings.WEBHOOK_URL))

    state = State(
        stream=stream,
        settings=settings,
        messagebus_factory=messagebus_factory,
        uow_factory=uow_factory,
        **optional_state,
    )

    # Configure stream ingester
    await exit_stack.enter_async_context(managed_stream_ingester(state))

    # Configure archive subscriber
    subscriber = ManagedSubscriber(
        connection_url=settings.RABBITMQ_DSN,
        message_handler=SubscriberMessageHandler(messagebus_factory),
    )
    await exit_stack.enter_async_context(subscriber)

    ctx["state"] = state
    ctx["exit_stack"] = exit_stack

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-state-manager"

    functions = [run_persist_export]

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
