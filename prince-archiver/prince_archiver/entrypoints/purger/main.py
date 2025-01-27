import logging
import os

from arq import ArqRedis, cron
from arq import create_pool
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import Stream
from prince_archiver.log import configure_logging
from prince_archiver.service_layer.streams import Streams

from .functions import State, delete_src
from .settings import Settings
from datetime import UTC, datetime, timedelta
from prince_archiver.service_layer.streams import IncomingMessage

LOGGER = logging.getLogger(__name__)




async def main():
    # Step 1: Initialize Redis connection
    redis = await create_pool(
        RedisSettings.from_dsn(os.getenv("REDIS_DSN", "redis://localhost:6379"))
    )

    # Step 2: Load settings
    settings = Settings()

    # Step 3: Initialize State object
    state = State(
        settings=settings,
        stream=Stream(redis=redis, name=Streams.imaging_events),
        path_manager=PathManager(settings.SRC_DIR),
    )
    end = datetime.now(tz=UTC) - state.settings.SRC_LIFESPAN
    start = end - timedelta(hours=3)
    LOGGER.info(f"end is {end} and start is {start}")
    await delete_src(ctx={"state": state})
    async for message in state.stream.range(start, end, msg_cls=IncomingMessage):
        data = message.processed_data()
        LOGGER.info(data)
