import logging
from typing import Callable

from prince_archiver.adapters.streams import AbstractIngester
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import ImportImagingEvent
from prince_archiver.service_layer.streams import IncomingExportMessage, IncomingMessage

LOGGER = logging.getLogger(__name__)


class Ingester(AbstractIngester):
    async def consume(self):
        async for message in self.streamer:
            try:
                await self.handler(message)
            except ServiceLayerException:
                pass


async def status_update_handler(
    message: IncomingExportMessage,
    *,
    messagebus_factory: Callable[[], MessageBus],
):
    messagebus = messagebus_factory()
    async with message.process():
        await messagebus.handle(message.processed_data())


async def import_handler(
    message: IncomingMessage,
    *,
    messagebus_factory: Callable[[], MessageBus],
):
    data = message.processed_data()
    src_dir_info = {
        "img_count": data.img_count,
        "local_path": data.local_path,
    }
    mapped_message = ImportImagingEvent(**dict(data), src_dir_info=src_dir_info)

    messagebus = messagebus_factory()
    async with message.process():
        await messagebus.handle(mapped_message)
