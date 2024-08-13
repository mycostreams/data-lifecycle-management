import logging
import os
from contextlib import AsyncExitStack

from arq.connections import RedisSettings

from prince_archiver.config import WorkerSettings as _Settings
from prince_archiver.config import get_worker_settings
from prince_archiver.definitions import EventType
from prince_archiver.dto import TimestepDTO
from prince_archiver.file import managed_file_system
from prince_archiver.logging import configure_logging
from prince_archiver.service_layer.messagebus import MessageBus, MessagebusFactoryT
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .dto import UploadDTO
from .handlers import UploadHandler, add_upload_to_db

LOGGER = logging.getLogger(__name__)


async def workflow(
    ctx: dict,
    input_data: dict,
):
    messagebus: MessageBus = ctx["messagebus"]
    settings: _Settings = ctx["settings"]

    data = TimestepDTO.model_validate(input_data)

    base_path = "images" if data.event_type == EventType.STITCH else "videos"

    message = UploadDTO(
        timestep_id=data.timestep_id,
        img_dir=settings.DATA_DIR / data.img_dir,
        key=f"{settings.AWS_BUCKET_NAME}/{base_path}/{data.key}",
    )
    await messagebus.handle(message)


async def startup(ctx):
    configure_logging()

    LOGGER.info("Starting up worker")

    exit_stack = await AsyncExitStack().__aenter__()

    settings = get_worker_settings()

    s3 = await exit_stack.enter_async_context(managed_file_system(settings))
    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    def _message_bus_factory():
        return MessageBus(
            handlers={
                UploadDTO: [UploadHandler(s3=s3), add_upload_to_db],
            },
            uow=UnitOfWork(sessionmaker),
        )

    ctx["settings"] = settings
    ctx["messagebus_factory"] = _message_bus_factory
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
