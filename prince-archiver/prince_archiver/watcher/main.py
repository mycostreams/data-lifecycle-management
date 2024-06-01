import asyncio
import logging
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from watchfiles import Change, awatch

from prince_archiver.config import WatcherSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.dto import TimestepDTO
from prince_archiver.logging import configure_logging
from prince_archiver.messagebus import MessageBus
from prince_archiver.utils import parse_timestep_dir

from .handlers import ArqHandler, add_to_db


async def amain(*, _settings: WatcherSettings | None = None):
    configure_logging()

    settings = _settings or WatcherSettings()

    redis = await create_pool(
        RedisSettings.from_dsn(str(settings.REDIS_DSN)),
    )

    messagebus = MessageBus(
        handlers={TimestepDTO: [add_to_db, ArqHandler(redis)]},
        uow=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    logging.info("Watching %s", settings.DATA_DIR)

    watcher = awatch(
        settings.DATA_DIR / "events",
        watch_filter=lambda change, _: change == Change.added,
        force_polling=settings.WATCHFILES_FORCE_POLLING,
        recursive=False,
    )
    async for changes in watcher:
        for _, _filepath in changes:
            filepath = Path(_filepath)

            data = parse_timestep_dir(filepath)
            await messagebus.handle(data)

            filepath.unlink()



def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
