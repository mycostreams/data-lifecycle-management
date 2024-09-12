import logging
import os
from contextlib import AsyncExitStack

from arq import ArqRedis, cron
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from prince_archiver.adapters.streams import Stream, Streams
from prince_archiver.log import configure_logging

from .functions import State, delete_src, run_trim
from .ingester import managed_watcher
from .settings import IngesterSettings

LOGGER = logging.getLogger(__name__)


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up data ingester")
    redis: ArqRedis = ctx["redis"]

    stack = await AsyncExitStack().__aenter__()
    settings = IngesterSettings()

    state = State(
        settings=settings,
        stream=Stream(
            redis=redis,
            stream=Streams.new_imaging_event,
        ),
    )

    await stack.enter_async_context(managed_watcher(state))

    ctx["state"] = state
    ctx["stack"] = stack


async def shutdown(ctx: dict):
    stack: AsyncExitStack = ctx["stack"]
    await stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-data-ingester"

    cron_jobs = [
        cron(delete_src, hour={0, 12}),
        # cron(delete_staging, second={0, 15, 30, 45}),
        cron(run_trim, hour={3, 15}, minute={0}),
    ]

    timezone = ZoneInfo("Europe/Amsterdam")

    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
