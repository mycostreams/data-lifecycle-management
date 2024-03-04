import logging
from pathlib import Path
from typing import Callable

from celery import chain

from prince_archiver.celery import tasks
from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.dto import TimestepDTO
from prince_archiver.models import Timestep
from prince_archiver.utils import parse_timestep_dir

LOGGER = logging.getLogger(__name__)


HandlerT = Callable[[TimestepDTO, AbstractUnitOfWork], None]


class NewTimestepHandler:

    def __init__(
        self,
        archive_dir: Path,
        unit_of_work: AbstractUnitOfWork,
        handlers: list[HandlerT],
    ):

        self.archive_dir = archive_dir
        self.unit_of_work = unit_of_work
        self.handlers = handlers

    def __call__(self, path: Path):

        base_dto = parse_timestep_dir(Path(path).parent.parent)

        LOGGER.info("New timestep %s", base_dto.experiment.id)

        archive_path = self.archive_dir / f"{base_dto.experiment.id}.tar"

        data = TimestepDTO(
            experiment_archive_path=archive_path,
            **base_dto.model_dump(by_alias=True),
        )

        for handler in self.handlers:
            handler(data, self.unit_of_work)


def add_to_db(data: TimestepDTO, unit_of_work: AbstractUnitOfWork) -> None:
    LOGGER.info("Saving %s to db", data.key)

    with unit_of_work:
        timestep = Timestep(
            experiment_id=data.experiment.id,
            key=data.archive_name,
            **data.model_dump(
                exclude={
                    "experiment",
                    "experiment_archive_path",
                    "archive_name",
                    "raw_img_path",
                }
            ),
        )

        unit_of_work.timestamps.add(timestep)
        unit_of_work.commit()


def archive_timestep(data: TimestepDTO, _: AbstractUnitOfWork) -> None:
    LOGGER.info("Initiating archiving of %s", data.key)

    serialized_data = data.model_dump(mode="json", by_alias=True)

    workflow = chain(
        tasks.archive_timestep.si(data=serialized_data),
        tasks.upload_to_object_store.si(data=serialized_data),
    )

    workflow.delay()
