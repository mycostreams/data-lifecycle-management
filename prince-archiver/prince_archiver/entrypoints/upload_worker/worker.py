import logging
import os
from contextlib import AsyncExitStack
from functools import partial

from arq.connections import RedisSettings

from prince_archiver.config import UploadWorkerSettings as Settings
from prince_archiver.file import managed_file_system
from prince_archiver.logging import configure_logging
from prince_archiver.models import init_mappers
from prince_archiver.service_layer.handlers.exporter import (
    Context,
    ExportHandler,
    initiate_imaging_event_export,
    key_generator,
    persist_imaging_event_export,
)
from prince_archiver.service_layer.messagebus import MessageBus, MessagebusFactoryT
from prince_archiver.service_layer.messages import (
    ExportedImagingEvent,
    ExportImagingEvent,
    InitiateExportEvent,
)
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

LOGGER = logging.getLogger(__name__)


async def workflow(
    ctx: dict,
    input_data: dict,
):
    messagebus: MessageBus = ctx["messagebus"]

    dto = InitiateExportEvent.model_validate(input_data)
    await messagebus.handle(dto)


async def startup(ctx: dict):
    configure_logging()
    init_mappers()

    LOGGER.info("Starting up worker")

    exit_stack = await AsyncExitStack().__aenter__()

    settings = Settings()
    s3 = await exit_stack.enter_async_context(managed_file_system(settings))
    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    messagebus_factory = MessageBus.factory(
        handlers={
            InitiateExportEvent: [
                partial(
                    initiate_imaging_event_export,
                    context=Context(
                        base_path=settings.DATA_DIR,
                        key_generator=partial(
                            key_generator,
                            settings.AWS_BUCKET_NAME,
                        ),
                    ),
                )
            ],
            ExportImagingEvent: [ExportHandler(s3)],
            ExportedImagingEvent: [persist_imaging_event_export],
        },
        uow=lambda: UnitOfWork(sessionmaker),
    )

    ctx["messagebus_factory"] = messagebus_factory
    ctx["exit_stack"] = exit_stack

    LOGGER.info("Start up complete")


async def on_job_start(ctx: dict):
    messagebus_factory: MessagebusFactoryT = ctx["messagebus_factory"]
    ctx["messagebus"] = messagebus_factory()


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    functions = [workflow]
    on_startup = startup
    on_shutdown = shutdown
    on_job_start = on_job_start

    keep_result = 0
    max_jobs = 2

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
