import logging

from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.service_layer.external_dto import UpdateArchiveEntries
from prince_archiver.service_layer.messagebus import MessagebusFactoryT

LOGGER = logging.getLogger(__name__)


class SubscriberMessageHandler:
    DTO_CLASS = UpdateArchiveEntries

    def __init__(
        self,
        messagebus_factory: MessagebusFactoryT,
    ):
        self.messagebus_factory = messagebus_factory

    async def __call__(self, message: AbstractIncomingMessage):
        async with message.process():
            try:
                await self._process(message.body)
            except Exception as err:
                LOGGER.exception(err)
                raise err

    async def _process(self, raw_message: bytes):
        messagebus = self.messagebus_factory()
        message = self.DTO_CLASS.model_validate_json(raw_message)
        await messagebus.handle(message)
