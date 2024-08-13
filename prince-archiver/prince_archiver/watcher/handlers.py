import logging
from datetime import UTC

from arq import ArqRedis

from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.dto import TimestepDTO
from prince_archiver.models import Timestep
from prince_archiver.service_layer.messagebus import AbstractHandler

LOGGER = logging.getLogger(__name__)


async def add_to_db(message: TimestepDTO, uow: AbstractUnitOfWork) -> None:
    LOGGER.info("Saving %s to db", message.key)
    async with uow:
        timestep = Timestep(
            local_dir=message.img_dir.as_posix(),
            img_count=message.img_count,
            timestamp=message.timestamp.astimezone(UTC),
            position=message.position,
            timestep_id=message.timestep_id,
            experiment_id=message.experiment_id,
        )
        uow.timestamps.add(timestep)
        await uow.commit()


class ArqHandler(AbstractHandler[TimestepDTO]):
    def __init__(self, client: ArqRedis):
        self.client = client

    async def __call__(self, message: TimestepDTO, _: AbstractUnitOfWork):
        LOGGER.info("Enqueing jobs %s", message.key)

        await self.client.enqueue_job(
            "workflow",
            message.model_dump(mode="json", by_alias=True),
        )
