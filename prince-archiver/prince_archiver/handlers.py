import logging
from typing import Callable

from celery import chain

from .celery import tasks
from .db import AbstractUnitOfWork
from .dto import TimestepDTO
from .models import Timestep

LOGGER = logging.getLogger(__name__)


HandlerT = Callable[[TimestepDTO, AbstractUnitOfWork], None]


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


DEFAULT_HANDLERS: list[HandlerT] = [
    add_to_db,
    archive_timestep,
]
