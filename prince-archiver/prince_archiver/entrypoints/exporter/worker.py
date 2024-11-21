import logging
import os
from contextlib import AsyncExitStack

from arq import ArqRedis, Retry
from arq.connections import RedisSettings

from prince_archiver.log import configure_logging
from prince_archiver.models import init_mappers
from prince_archiver.service_layer.dto import ExportImagingEvent

from .settings import Settings
from .state import State, get_managed_state

LOGGER = logging.getLogger(__name__)


async def run_export(
    ctx: dict,
    input_data: dict,
):
    dto = ExportImagingEvent.model_validate(input_data)
    state: State = ctx["state"]

    try:
        await state.export_handler.process(dto)
    except* (OSError, TimeoutError) as exc:
        job_try: int = ctx.get("job_try", 1)
        raise Retry(defer=job_try * (3 * 60)) from exc


async def startup(ctx: dict):
    configure_logging()
    init_mappers()

    LOGGER.info("Starting up worker")

    redis: ArqRedis = ctx["redis"]

    settings = Settings()
    exit_stack = await AsyncExitStack().__aenter__()

    state = await exit_stack.enter_async_context(
        get_managed_state(redis, settings=settings),
    )

    # Consume stream
    await exit_stack.enter_async_context(state.stream_ingester.managed_consumer())

    ctx["state"] = state
    ctx["exit_stack"] = exit_stack

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    state: State = ctx["state"]
    state.stop_event.set()

    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-exporter"

    functions = [run_export]
    on_startup = startup
    on_shutdown = shutdown

    keep_result = 0
    max_retries = 5
    max_jobs = 2

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
