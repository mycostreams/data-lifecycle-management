import asyncio
import logging
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from watchfiles import awatch

from prince_archiver.config import WatcherSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.logging import configure_logging
from prince_archiver.watcher import (
    ArqHandler,
    TimestepHandler,
    add_to_db,
    filter_on_final_image,
)


async def main(*, _settings: WatcherSettings | None = None):

    configure_logging()

    settings = _settings or WatcherSettings()

    redis = await create_pool(
        RedisSettings.from_dsn(str(settings.REDIS_DSN)),
    )

    handler = TimestepHandler(
        handlers=[add_to_db, ArqHandler(redis)],
        unit_of_work=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    logging.info("Watching %s", settings.DATA_DIR)

    watcher = awatch(settings.DATA_DIR, watch_filter=filter_on_final_image)
    async for changes in watcher:
        for _, filepath in changes:
            await handler(Path(filepath).parent.parent)


if __name__ == "__main__":
    asyncio.run(main())
