import logging
import os
from contextlib import AsyncExitStack

from arq import ArqRedis
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from prince_archiver.log import configure_logging
from prince_archiver.models import init_mappers

from .settings import Settings
from .state import State, get_managed_state

LOGGER = logging.getLogger(__name__)


async def run_heartbeat(_: dict):
    LOGGER.info("HEARTBEAT")


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

    # Configure consumers
    await exit_stack.enter_async_context(state.import_ingester.managed_consumer())
    await exit_stack.enter_async_context(state.export_ingester.managed_consumer())
    await exit_stack.enter_async_context(state.subscriber)

    ctx["state"] = state
    ctx["exit_stack"] = exit_stack

    LOGGER.info("Start up complete")


async def shutdown(ctx: dict):
    state: State = ctx["state"]
    state.stop_event.set()

    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-state-manager"

    functions = [run_heartbeat]

    on_startup = startup
    on_shutdown = shutdown

    timezone = ZoneInfo("Europe/Amsterdam")

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
