"""Handlers used to export imaging event bundles."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Protocol

from arq import ArqRedis

from prince_archiver.adapters.streams import ConsumerGroup, Stream
from prince_archiver.service_layer.messages import ExportImagingEvent
from prince_archiver.service_layer.streams import Group, IncomingMessage

LOGGER = logging.getLogger(__name__)


class State(Protocol):
    stream: Stream
    arq_redis: ArqRedis


async def stream_ingester(state: State):
    """Ingest message from stream and add to queue."""
    group = ConsumerGroup(
        group_name=Group.export_event,
        consumer_name=Group.export_event,
    )
    async for msg in state.stream.stream_group(group, msg_cls=IncomingMessage):
        async with msg.process():
            data = msg.processed_data()
            mapped_msg = ExportImagingEvent(
                **data.model_dump(),
                staging_path=data.src_dir_info.staging_path,
                local_path=data.src_dir_info.local_path,
            )

            LOGGER.info("[%s] Adding to queue", mapped_msg.ref_id)
            await state.arq_redis.enqueue_job(
                "run_export",
                mapped_msg.model_dump(mode="json"),
            )


@asynccontextmanager
async def managed_stream_ingester(state: State):
    LOGGER.info("Consuming stream")

    task = asyncio.create_task(stream_ingester(state))

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
