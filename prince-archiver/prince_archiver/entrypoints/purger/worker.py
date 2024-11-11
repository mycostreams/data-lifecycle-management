import logging
import os
from contextlib import AsyncExitStack

from arq import ArqRedis, cron
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import Stream
from prince_archiver.log import configure_logging
from prince_archiver.service_layer.streams import Streams

from .functions import State, delete_src
from .settings import Settings

LOGGER = logging.getLogger(__name__)


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up data ingester")
    redis: ArqRedis = ctx["redis"]

    stack = await AsyncExitStack().__aenter__()
    settings = Settings()

    stack = AsyncExitStack()

    state = State(
        settings=settings,
        stream=Stream(redis=redis, name=Streams.imaging_events),
        path_manager=PathManager(settings.SRC_DIR),
    )

    ctx["state"] = state
    ctx["stack"] = stack


async def shutdown(ctx: dict):
    stack: AsyncExitStack = ctx["stack"]
    await stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-event-ingester"

    cron_jobs = [
        cron(delete_src, hour={*range(0, 24, 2)}, minute={0}),
    ]

    timezone = ZoneInfo("Europe/Amsterdam")

    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
