import logging
from pathlib import Path
from typing import Callable

from celery import chain

from prince_archiver.celery import tasks
from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.dto import TimestepDTO
from prince_archiver.models import Timestep
from prince_archiver.utils import get_random_id, parse_timestep_dir

LOGGER = logging.getLogger(__name__)


HandlerT = Callable[[TimestepDTO, AbstractUnitOfWork], None]


class TimestepHandler:

    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        handlers: list[HandlerT],
    ):
        self.unit_of_work = unit_of_work
        self.handlers = handlers

    def __call__(self, path: Path):

        data = parse_timestep_dir(path)

        LOGGER.info("New timestep %s", data.experiment.id)

        for handler in self.handlers:
            handler(data, self.unit_of_work)


def add_to_db(data: TimestepDTO, unit_of_work: AbstractUnitOfWork) -> None:
    LOGGER.info("Saving %s to db", data.key)

    with unit_of_work:
        timestep = Timestep(
            experiment_id=data.experiment.id,
            **data.model_dump(),
        )

        unit_of_work.timestamps.add(timestep)
        unit_of_work.commit()


def archive_timestep(data: TimestepDTO, _: AbstractUnitOfWork) -> None:
    LOGGER.info("Initiating archiving of %s", data.key)

    files = list(
        (data.base_path / data.timestep_dir_name / data.img_dir_name).glob(".tif")
    )

    random_dir_name = get_random_id()
    compress_args = ((p, f"{random_dir_name}/{p.name}") for p in files)

    workflow = chain(
        tasks.compress_image.starmap(compress_args),
        tasks.archive_images.si(random_dir_name, data.key),
        tasks.upload_to_s3.si(data.key, data.key),
    )

    workflow.delay()
