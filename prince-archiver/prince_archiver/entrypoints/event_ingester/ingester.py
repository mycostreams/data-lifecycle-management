import asyncio
import logging
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncGenerator, Protocol

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.ingester import (
    EventFile,
    EventIngester,
    managed_event_queue,
)
from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.messages import ImagingEventStream, SrcDirInfo
from prince_archiver.service_layer.streams import Message

from .settings import Settings

LOGGER = logging.getLogger(__name__)


class State(Protocol):
    settings: Settings
    stream: Stream
    path_manager: PathManager


async def process(event_file: EventFile, *, state: State):
    """Process new imaging event.

    Copy to staging if necessary and add to stream.

    """
    async with event_file.process() as (dto, src_dir):
        LOGGER.info("[%s] Adding to stream", dto.timestep_id)

        target_dir = f"{int(dto.timestamp.timestamp())}-{dto.timestep_id.hex[:6]}"
        metadata = await src_dir.get_metadata()

        # Prep the export message export message
        msg = ImagingEventStream(
            ref_id=dto.timestep_id,
            experiment_id=dto.experiment_id,
            timestamp=dto.timestamp,
            system=event_file.system_dir.system,
            src_dir_info=SrcDirInfo(
                staging_path=target_dir if state.settings.COPY_TO_STAGING else None,
                local_path=dto.img_dir,
                raw_metadata=metadata,
                img_count=dto.img_count,
            ),
        )

        # Copy to staging
        if state.settings.COPY_TO_STAGING:
            await src_dir.copy(state.path_manager.get_staging_path() / target_dir)

        await state.stream.add(Message(msg))

    LOGGER.info("[%s] Added to stream", dto.timestep_id)


@asynccontextmanager
async def managed_event_ingester(state: State) -> AsyncGenerator[EventIngester, None]:
    handler = partial(process, state=state)
    async with managed_event_queue(handler) as event_queue:
        yield EventIngester(
            state.path_manager.get_system_dirs(),
            handler=event_queue.add,
        )


@asynccontextmanager
async def managed_background_event_ingester(
    event_ingester: EventIngester,
    *,
    stop_event: asyncio.Event | None = None,
) -> AsyncGenerator[None, None]:
    stop_event = stop_event or asyncio.Event()

    backlog_task = asyncio.create_task(event_ingester.ingest_backlog())
    task = asyncio.create_task(event_ingester.ingest_latest(stop_event=stop_event))

    yield

    LOGGER.info("Stopping watching")

    stop_event.set()
    await asyncio.gather(backlog_task, task, return_exceptions=True)

    LOGGER.info("Stopped watching")
