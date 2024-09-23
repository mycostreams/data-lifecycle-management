import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Protocol

from prince_archiver.adapters.ingester import EventFile, EventIngester
from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.messages import ImagingEventStream, SrcDirInfo
from prince_archiver.service_layer.streams import Message

from .settings import Settings

LOGGER = logging.getLogger(__name__)


class State(Protocol):
    settings: Settings
    stream: Stream


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
                staging_path=target_dir if state.settings.STAGING_DIR else None,
                local_path=dto.img_dir,
                raw_metadata=metadata,
                img_count=dto.img_count,
            ),
        )

        # Copy to staging
        if state.settings.STAGING_DIR:
            await src_dir.copy(state.settings.STAGING_DIR / target_dir)

        await state.stream.add(Message(msg))

    LOGGER.info("[%s] Added to stream", dto.timestep_id)


@asynccontextmanager
async def managed_ingester(
    event_ingester: EventIngester,
    *,
    stop_event: asyncio.Event | None = None,
):
    stop_event = stop_event or asyncio.Event()

    task = asyncio.create_task(event_ingester.ingest_latest(stop_event=stop_event))

    yield

    LOGGER.info("Stopping watching")
    stop_event.set()
    await task

    LOGGER.info("Stopped watching")
