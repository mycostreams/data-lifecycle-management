from typing import Callable
import logging

from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.messagebus import MessageBus
from prince_archiver.models import DataArchiveEntry, Timestep

from .dto import Message


LOGGER = logging.getLogger(__name__)


class MessageHandler:

    def __init__(
        self,
        messagebus_factory: Callable[[], MessageBus],
    ):
        self.messagebus_factory = messagebus_factory

    async def __call__(self, message: AbstractIncomingMessage):
        messagebus = self.messagebus_factory()
        async with message.process():
            data = Message.model_validate_json(message.body)
            LOGGER.info("Message received: %s", data.job_id)
            await messagebus.handle(data)


async def update_data_archive_entries(message: Message, uow: AbstractUnitOfWork):
    async with uow:
        timesteps = await uow.timestamps.get_by_date(message.date)

        mapped_timesteps: dict[str, Timestep] = {}
        for item in timesteps:
            if obj := item.object_store_entry:
                mapped_timesteps[f"{obj.bucket}/{obj.key}"] = item
        persisted_keys = mapped_timesteps.keys()

        for archive in message.archives:
            for key in filter(lambda key: key in persisted_keys, archive.src_keys):
                mapped_timesteps[key].data_archive_entry = DataArchiveEntry(
                    job_id=message.job_id,
                    path=archive.path,
                    file=key,
                )

        await uow.commit()
