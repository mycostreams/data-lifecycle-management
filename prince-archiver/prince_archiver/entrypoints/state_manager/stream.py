import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Callable

from prince_archiver.adapters.streams import Consumer, Stream
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import ImportImagingEvent
from prince_archiver.service_layer.streams import Group, IncomingMessage

LOGGER = logging.getLogger(__name__)


class StreamMessageHandler:
    def __init__(self, message_bus_factory: Callable[[], MessageBus]):
        self.messagebus_factory = message_bus_factory

    async def process(self, message: IncomingMessage):
        data = message.processed_data()
        src_dir_info = {
            "img_count": data.img_count,
            "local_path": data.local_path,
        }
        mapped_message = ImportImagingEvent(**dict(data), src_dir_info=src_dir_info)

        messagebus = self.messagebus_factory()
        async with message.process():
            await messagebus.handle(mapped_message)


async def stream_ingester(stream: Stream, handler: StreamMessageHandler):
    LOGGER.info("Ingesting stream")

    consumer = Consumer(group_name=Group.import_event)

    async for message in stream.stream_group(consumer, msg_cls=IncomingMessage):
        try:
            await handler.process(message)
        except ServiceLayerException:
            pass


@asynccontextmanager
async def managed_stream_ingester(stream: Stream, handler: StreamMessageHandler):
    task = asyncio.create_task(stream_ingester(stream, handler))

    yield

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass
