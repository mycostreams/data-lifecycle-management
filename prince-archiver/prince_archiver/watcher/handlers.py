import logging
from datetime import UTC

from arq import ArqRedis

from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.dto import TimestepDTO
from prince_archiver.messagebus import AbstractHandler
from prince_archiver.models import Timestep

LOGGER = logging.getLogger(__name__)


async def add_to_db(message: TimestepDTO, unit_of_work: AbstractUnitOfWork) -> None:
    LOGGER.info("Saving %s to db", message.key)
    async with unit_of_work:
        timestep = Timestep(
            local_dir=message.timestep_dir_name,
            img_count=message.img_count,
            timestamp=message.timestamp.astimezone(UTC),
            position=message.position,
            timestep_id=message.timestep_id,
            experiment_id=message.experiment_id,
        )
        unit_of_work.timestamps.add(timestep)
        await unit_of_work.commit()


class ArqHandler(AbstractHandler[TimestepDTO]):

    def __init__(self, client: ArqRedis):
        self.client = client

    async def __call__(self, message: TimestepDTO, _: AbstractUnitOfWork):
        LOGGER.info("Enqueing jobs %s", message.key)

        await self.client.enqueue_job(
            "workflow",
            message.model_dump(mode="json", by_alias=True),
        )
