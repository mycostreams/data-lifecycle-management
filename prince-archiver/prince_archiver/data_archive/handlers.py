import logging
from typing import Callable

from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.models import (
    DataArchiveEntry,
    Timestep,
)
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.uow import AbstractUnitOfWork

from .dto import UpdateArchiveEntries

LOGGER = logging.getLogger(__name__)


class SubscriberMessageHandler:
    DTO_CLASS = UpdateArchiveEntries

    def __init__(
        self,
        messagebus_factory: Callable[[], MessageBus],
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


async def add_data_archive_entries(
    message: UpdateArchiveEntries,
    uow: AbstractUnitOfWork,
):
    async with uow:
        LOGGER.info("[%s] Updating archive entries", message.job_id)

        timesteps = await uow.timestamps.get_by_date(message.date)

        mapped_timesteps: dict[str, Timestep] = {}
        for item in timesteps:
            if obj := item.object_store_entry:
                mapped_timesteps[obj.key] = item
        persisted_keys = mapped_timesteps.keys()

        for archive in message.archives:
            for key in filter(lambda key: key in persisted_keys, archive.src_keys):
                timestep = mapped_timesteps[key]
                if timestep.data_archive_entry:
                    msg = "[%s] Timestep already associated to archive %s"
                    LOGGER.info(msg, message.job_id, key)
                    continue

                timestep.data_archive_entry = DataArchiveEntry(
                    job_id=message.job_id,
                    archive_path=archive.path,
                    file=key,
                )

        await uow.commit()
