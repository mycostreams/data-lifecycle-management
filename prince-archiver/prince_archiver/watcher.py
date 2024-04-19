import logging
from datetime import UTC
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


def filter_on_param_file(change: Change, path: str) -> bool:
    return change == Change.added and Path(path).name == "param.json"


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

        LOGGER.info("New timestep %s", data.experiment_id)

        for handler in self.handlers:
            await handler(data, self.unit_of_work)


async def add_to_db(data: TimestepDTO, unit_of_work: AbstractUnitOfWork) -> None:
    LOGGER.info("Saving %s to db", data.key)

    async with unit_of_work:
        timestep = Timestep(
            src_dir=data.timestep_dir_name,
            timestamp=data.timestamp.astimezone(UTC),
            **data.model_dump(
                exclude={
                    "cross_date",
                    "img_dir_name",
                    "plate",
                    "timestamp",
                    "timestep_dir_name",
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
