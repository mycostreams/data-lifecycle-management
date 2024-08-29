import asyncio
import logging
from pathlib import Path

from watchfiles import Change, awatch

from prince_archiver.config import WatcherSettings
from prince_archiver.logging import configure_logging
from prince_archiver.service_layer.messages import ImportImagingEvent, SrcDirInfo
from prince_archiver.utils import parse_timestep_dir

from .context import Context, managed_context


async def process_backlog(context: Context):
    for filepath in context.settings.EVENTS_DIR.iterdir():
        await process(filepath, context)


async def process(filepath: Path, context: Context):
    dto = parse_timestep_dir(filepath)

    raw_metadata = await context.file_manager.get_raw_metadata(
        context.file_manager.get_src_path(dto.img_dir),
    )

    await context.messagebus.handle(
        ImportImagingEvent(
            ref_id=dto.timestep_id,
            experiment_id=dto.experiment_id,
            timestamp=dto.timestamp,
            src_dir_info=SrcDirInfo(
                local_path=dto.img_dir,
                raw_metadata=raw_metadata,
                img_count=dto.img_count,
            ),
        )
    )

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
            process(Path(_filepath), context=context)


async def amain(*, _settings: WatcherSettings | None = None):
    async with managed_context(_settings=_settings) as context:
        logging.info("Watching %s", context.settings.DATA_DIR)
        await watch(context)


def main():
    configure_logging()
    asyncio.run(amain())


if __name__ == "__main__":
    main()
