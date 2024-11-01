"""Handlers used to export imaging event bundles."""

import asyncio
import logging
from contextlib import asynccontextmanager

from arq import ArqRedis

from prince_archiver.adapters.streams import Consumer, Stream
from prince_archiver.service_layer.messages import ExportImagingEvent
from prince_archiver.service_layer.streams import Group, IncomingMessage

LOGGER = logging.getLogger(__name__)


class StreamMessageHandler:
    def __init__(self, redis: ArqRedis):
        self.redis = redis

    async def process(self, message: IncomingMessage):
        mapped_msg = ExportImagingEvent(
            **dict(message.processed_data()),
            message_info=message.info.__dict__,
        )
        await self.redis.enqueue_job(
            "run_export",
            mapped_msg.model_dump(mode="json"),
        )


async def stream_ingester(stream: Stream, handler: StreamMessageHandler):
    """Ingest message from stream and add to queue."""
    consumer = Consumer(group_name=Group.export_event)
    async for msg in stream.stream_group(consumer, msg_cls=IncomingMessage):
        await handler.process(msg)


@asynccontextmanager
async def managed_stream_ingester(
    stream: Stream,
    handler: StreamMessageHandler,
):
    LOGGER.info("Consuming stream")

    task = asyncio.create_task(stream_ingester(stream, handler))

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
