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
    path_obj = Path(path)

    is_added = change == Change.added
    is_param_file = path_obj.name == "param.json"

    return is_added and is_param_file


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
            local_dir=data.timestep_dir_name,
            img_count=data.img_count,
            timestamp=data.timestamp.astimezone(UTC),
            position=data.position,
            timestep_id=data.timestep_id,
            experiment_id=data.experiment_id,
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
