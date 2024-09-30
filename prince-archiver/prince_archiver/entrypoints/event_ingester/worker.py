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

from .functions import State, run_trim
from .ingester import managed_background_event_ingester, managed_event_ingester
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
        stream=Stream(
            redis=redis,
            stream=Streams.new_imaging_event,
        ),
        path_manager=PathManager(settings.SRC_DIR),
    )

    # Setup data ingester
    event_ingester = await stack.enter_async_context(managed_event_ingester(state))
    await stack.enter_async_context(managed_background_event_ingester(event_ingester))

    ctx["state"] = state
    ctx["stack"] = stack


async def shutdown(ctx: dict):
    stack: AsyncExitStack = ctx["stack"]
    await stack.aclose()


class WorkerSettings:
    queue_name = "arq:queue-event-ingester"

    cron_jobs = [
        # cron(delete_src, hour={*range(0, 24, 2)}, minute={0}),
        # cron(delete_staging, second={0, 15, 30, 45}),
        cron(run_trim, hour={3, 15}, minute={0}),
    ]

    timezone = ZoneInfo("Europe/Amsterdam")

    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
