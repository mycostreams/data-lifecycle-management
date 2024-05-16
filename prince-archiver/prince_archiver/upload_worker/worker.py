import logging
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack

from arq.connections import RedisSettings

from prince_archiver.config import get_worker_settings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.dto import TimestepDTO
from prince_archiver.file import managed_file_system
from prince_archiver.logging import configure_logging
from prince_archiver.messagebus import MessageBus, MessagebusFactoryT

from .dto import UploadDTO
from .handlers import UploadHandler, add_upload_to_db

LOGGER = logging.getLogger(__name__)


async def workflow(
    ctx: dict,
    input_data: dict,
):
    data = TimestepDTO.model_validate(input_data)
    messagebus: MessageBus = ctx["messagebus"]
    await messagebus.handle(data)


async def startup(ctx):
    configure_logging()

    LOGGER.info("Starting up worker")

    exit_stack = await AsyncExitStack().__aenter__()

    settings = get_worker_settings()
    pool = exit_stack.enter_context(ProcessPoolExecutor())
    s3 = await exit_stack.enter_async_context(managed_file_system(settings))
    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    def _message_bus_factory():
        return MessageBus(
            handlers={
                UploadDTO: [add_upload_to_db],
                TimestepDTO: [
                    UploadHandler(
                        s3=s3,
                        bucket_name=settings.AWS_BUCKET_NAME,
                        pool=pool,
                        base_dir=settings.DATA_DIR,
                    ),
                ],
            },
            uow=UnitOfWork(sessionmaker),
        )

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
    max_jobs = 2
    on_startup = startup
    on_shutdown = shutdown
    on_job_start = on_job_start

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
