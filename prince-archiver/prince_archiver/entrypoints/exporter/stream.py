"""Handlers used to export imaging event bundles."""

import logging

from arq import ArqRedis

from prince_archiver.adapters.streams import AbstractIngester
from prince_archiver.service_layer.dto import ExportImagingEvent
from prince_archiver.service_layer.streams import IncomingMessage

LOGGER = logging.getLogger(__name__)


class Ingester(AbstractIngester):
    async def consume(self):
        async for message in self.streamer:
            try:
                await self.handler(message)
            except Exception as exc:
                LOGGER.exception(exc)


async def message_handler(message: IncomingMessage, *, redis: ArqRedis):
    mapped_msg = ExportImagingEvent(
        **dict(message.processed_data()),
        message_info=message.info.__dict__,
    )
    await redis.enqueue_job(
        "run_export",
        mapped_msg.model_dump(mode="json"),
    )
