import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from prince_archiver.adapters.ingester import EventFile, EventIngester
from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.messages import ImagingEventStream, SrcDirInfo
from prince_archiver.service_layer.streams import Message

LOGGER = logging.getLogger(__name__)


class EventIngesterHandler:
    def __init__(
        self,
        stream: Stream,
        staging_path: Path | None,
    ):
        self.stream = stream
        self.staging_path = staging_path

    async def process(self, event_file: EventFile):
        async with event_file.process() as (dto, src_dir):
            LOGGER.info("[%s] Adding to stream", dto.timestep_id)

            target_dir = f"{int(dto.timestamp.timestamp())}-{dto.timestep_id.hex[:6]}"

            # Prep the export message export message
            msg = ImagingEventStream(
                ref_id=dto.timestep_id,
                type=dto.event_type,
                experiment_id=dto.experiment_id,
                timestamp=dto.timestamp,
                system=event_file.system_dir.system,
                src_dir_info=SrcDirInfo(
                    staging_path=target_dir if self.staging_path else None,
                    local_path=dto.img_dir,
                    raw_metadata=dto.model_dump(mode="json", by_alias=True),
                    img_count=dto.img_count,
                ),
            )

            # Copy files if necessary
            await src_dir.write_metadata(dto.model_dump_json(by_alias=True))
            if self.staging_path:
                await src_dir.copy(self.staging_path / target_dir)

            await self.stream.add(Message(msg))


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
