import logging
import os
from contextlib import AsyncExitStack
from dataclasses import dataclass
from functools import partial

from arq import ArqRedis, Retry
from arq.connections import RedisSettings
from botocore.exceptions import ConnectTimeoutError

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import Stream
from prince_archiver.file import managed_file_system
from prince_archiver.log import configure_logging
from prince_archiver.models import init_mappers
from prince_archiver.service_layer.handlers.export import ExportHandler
from prince_archiver.service_layer.handlers.utils import get_target_key
from prince_archiver.service_layer.messages import ExportImagingEvent
from prince_archiver.service_layer.streams import Streams

from .settings import Settings
from .stream import managed_stream_ingester

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    arq_redis: ArqRedis
    stream: Stream
    export_handler: ExportHandler


async def run_export(
    ctx: dict,
    input_data: dict,
):
    dto = ExportImagingEvent.model_validate(input_data)
    state: State = ctx["state"]

    try:
        await state.export_handler(dto)
    except (ConnectTimeoutError, OSError) as err:
        job_try: int = ctx.get("job_try", 1)
        raise Retry(defer=job_try * (3 * 60)) from err


async def startup(ctx: dict):
    configure_logging()
    init_mappers()

    LOGGER.info("Starting up worker")

    exit_stack = await AsyncExitStack().__aenter__()

    settings = Settings()

    s3 = await exit_stack.enter_async_context(managed_file_system(settings))
    redis: ArqRedis = ctx["redis"]

    state = State(
        arq_redis=redis,
        stream=Stream(
            redis=redis,
            stream=Streams.new_imaging_event,
        ),
        export_handler=ExportHandler(
            redis=redis,
            s3=s3,
            key_generator=partial(
                get_target_key,
                bucket=settings.AWS_BUCKET_NAME,
            ),
            path_manager=PathManager(settings.SRC_DIR),
        ),
    )

    # Consume stream
    await exit_stack.enter_async_context(managed_stream_ingester(state))

    ctx["state"] = state
    ctx["exit_stack"] = exit_stack

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    functions = [run_export]
    on_startup = startup
    on_shutdown = shutdown

    keep_result = 0
    max_retries = 1
    max_jobs = 5

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
