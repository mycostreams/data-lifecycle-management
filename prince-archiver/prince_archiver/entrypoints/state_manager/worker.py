import logging
import os
from contextlib import AsyncExitStack

from arq import ArqRedis
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from prince_archiver.log import configure_logging
from prince_archiver.models import init_mappers

from .functions import run_persist_export
from .settings import Settings
from .state import get_managed_state
from .stream import managed_stream_ingester

LOGGER = logging.getLogger(__name__)


async def startup(ctx: dict):
    configure_logging()
    init_mappers()

    LOGGER.info("Starting up")

    exit_stack = await AsyncExitStack().__aenter__()

    settings = Settings()
    redis: ArqRedis = ctx["redis"]

    state = await exit_stack.enter_async_context(
        get_managed_state(redis, settings=settings),
    )

    # Configure stream ingester
    await exit_stack.enter_async_context(
        managed_stream_ingester(state.stream, state.stream_message_handler)
    )

    # Configure archive subscriber
    await exit_stack.enter_async_context(state.subscriber)

    ctx["state"] = state
    ctx["exit_stack"] = exit_stack

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-state-manager"

    functions = [run_persist_export]

    on_startup = startup
    on_shutdown = shutdown

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
