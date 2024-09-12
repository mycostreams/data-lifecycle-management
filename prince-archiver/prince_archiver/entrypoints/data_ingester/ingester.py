import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Protocol

from watchfiles import Change, awatch

from prince_archiver.adapters.file import ArchiveFileManager, SrcPath
from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.external_dto import TimestepDTO
from prince_archiver.service_layer.messages import ImagingEventStream, SrcDirInfo

from .settings import IngesterSettings

LOGGER = logging.getLogger(__name__)


class State(Protocol):
    settings: IngesterSettings
    file_system: ArchiveFileManager
    stream: Stream
    event: asyncio.Event


def added_filter(change: Change, path: str) -> bool:
    return change == Change.added and Path(path).exists()


async def process(filepath: Path, state: State):
    """Process new imaging event.

    Copy to staging if necessary and add to stream.

    """
    dto = TimestepDTO.model_validate_json(filepath.read_text())

    LOGGER.info("[%s] Adding to stream", dto.timestep_id)

    src_dir = SrcPath(filepath.parent.parent / dto.img_dir)
    raw_metadata = await state.file_system.get_raw_metadata(src_dir)

    target_dir = f"{int(dto.timestamp.timestamp())}-{dto.timestep_id.hex[:6]}"
    if state.settings.STAGING_DIR:
        await state.file_system.copy_tree(
            src_dir,
            state.settings.STAGING_DIR / target_dir,
        )

    # Export message
    msg = ImagingEventStream(
        ref_id=dto.timestep_id,
        experiment_id=dto.experiment_id,
        timestamp=dto.timestamp,
        system=dto.system,
        src_dir_info=SrcDirInfo(
            staging_path=target_dir if state.settings.STAGING_DIR else None,
            local_path=dto.img_dir,
            raw_metadata=raw_metadata,
            img_count=dto.img_count,
        ),
    )
    await state.stream.add(msg)

    # Delete src json
    await state.file_system.rm(filepath)

    LOGGER.info("[%s] Added to stream", msg.ref_id)


async def watch(state: State):
    LOGGER.info("Starting watching")
    watcher = awatch(
        state.settings.PRINCE_DIR / "events",
        stop_event=state.event,
        watch_filter=added_filter,
        recursive=False,
    )
    async for changes in watcher:
        for _, _filepath in changes:
            await process(Path(_filepath), state)


@asynccontextmanager
async def managed_watcher(state: State):
    task = asyncio.create_task(watch(state))

    yield

    LOGGER.info("Stopping watching")
    state.event.set()
    await task
