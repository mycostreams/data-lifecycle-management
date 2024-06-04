import asyncio
import logging
from pathlib import Path

from watchfiles import Change, awatch

from prince_archiver.config import WatcherSettings
from prince_archiver.logging import configure_logging
from prince_archiver.utils import parse_timestep_dir

from .context import Context, managed_context


async def process_backlog(context: Context):

    for filepath in context.settings.EVENTS_DIR.iterdir():
        data = parse_timestep_dir(filepath)
        await context.messagebus.handle(data)

        filepath.unlink()


async def watch(context: Context):
    watcher = awatch(
        context.settings.EVENTS_DIR,
        watch_filter=lambda change, _: change == Change.added,
        force_polling=context.settings.WATCHFILES_FORCE_POLLING,
        recursive=False,
    )
    async for changes in watcher:
        for _, _filepath in changes:
            filepath = Path(_filepath)

            data = parse_timestep_dir(filepath)
            await context.messagebus.handle(data)

            filepath.unlink()


async def amain(*, _settings: WatcherSettings | None = None):
    async with managed_context(_settings=_settings) as context:
        logging.info("Watching %s", context.settings.DATA_DIR)
        await watch(context)


def main():
    configure_logging()
    asyncio.run(amain())


if __name__ == "__main__":
    main()
