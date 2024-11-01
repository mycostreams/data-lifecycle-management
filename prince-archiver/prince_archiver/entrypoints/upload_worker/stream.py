"""Handlers used to export imaging event bundles."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Protocol

from prince_archiver.adapters.streams import Consumer, Stream
from prince_archiver.service_layer.export import StreamMessageHandler
from prince_archiver.service_layer.streams import Group, IncomingMessage

LOGGER = logging.getLogger(__name__)


class State(Protocol):
    stream: Stream
    stream_message_handler: StreamMessageHandler


async def stream_ingester(state: State):
    """Ingest message from stream and add to queue."""
    consumer = Consumer(group_name=Group.export_event)
    async for msg in state.stream.stream_group(consumer, msg_cls=IncomingMessage):
        await state.stream_message_handler.process(msg)


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
