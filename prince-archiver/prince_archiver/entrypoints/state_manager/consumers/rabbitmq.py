import logging
from typing import Generator

from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.service_layer.dto import (
    AddDataArchiveEntry,
    NewDataArchiveEntries,
)
from prince_archiver.service_layer.messagebus import MessagebusFactoryT

LOGGER = logging.getLogger(__name__)


class SubscriberMessageHandler:
    DTO_CLASS = NewDataArchiveEntries

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
        for message in self._map_external_dto(raw_message):
            messagebus = self.messagebus_factory()
            await messagebus.handle(message)

    def _map_external_dto(
        self,
        raw_message: bytes,
    ) -> Generator[AddDataArchiveEntry, None, None]:
        message = self.DTO_CLASS.model_validate_json(raw_message)
        for archive in message.archives:
            yield AddDataArchiveEntry(
                id=archive.id,
                path=archive.path,
                job_id=message.job_id,
                members=[self._get_member(key) for key in archive.src_keys],
            )

    @staticmethod
    def _get_member(key: str) -> dict[str, str]:
        return {"src_key": key, "member_key": key.split("/")[-1]}
