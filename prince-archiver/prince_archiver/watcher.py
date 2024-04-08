import logging
from pathlib import Path
from typing import Awaitable, Callable

from arq import ArqRedis
from watchfiles import Change

from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.dto import TimestepDTO
from prince_archiver.models import Timestep
from prince_archiver.utils import parse_timestep_dir

LOGGER = logging.getLogger(__name__)


HandlerT = Callable[[TimestepDTO, AbstractUnitOfWork], Awaitable[None]]


def filter_on_final_image(change: Change, path: str) -> bool:
    return change == Change.added and Path(path).name == "Img_r10_c15.tif"


class TimestepHandler:

    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        handlers: list[HandlerT],
    ):
        self.unit_of_work = unit_of_work
        self.handlers = handlers

    async def __call__(self, path: Path):

        data = parse_timestep_dir(path)

        LOGGER.info("New timestep %s", data.experiment.id)

        for handler in self.handlers:
            await handler(data, self.unit_of_work)


async def add_to_db(data: TimestepDTO, unit_of_work: AbstractUnitOfWork) -> None:
    LOGGER.info("Saving %s to db", data.key)

    async with unit_of_work:
        timestep = Timestep(
            experiment_id=data.experiment.id,
            **data.model_dump(
                by_alias=True,
                exclude={
                    "experiment",
                    "base_path",
                    "timestep_dir_name",
                    "img_dir_name",
                },
            ),
        )
        unit_of_work.timestamps.add(timestep)
        await unit_of_work.commit()


class ArqHandler:

    def __init__(self, client: ArqRedis):
        self.client = client

    async def __call__(self, data: TimestepDTO, _: AbstractUnitOfWork):
        await self.client.enqueue_job(
            "workflow",
            data.model_dump(mode="json", by_alias=True),
        )
