"""Celery application."""

from pathlib import Path
from uuid import uuid4

from celery import Celery, chain, group, signals
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from prince_archiver.config import Settings
from prince_archiver.dto import Archive, ArchivedPlateTimestep, PlateTimestep
from prince_archiver.utils import get_plate_timesteps

from .task import AbstractTask, CustomTask

LOGGER = get_task_logger(__name__)

celery_app = Celery("worker")
celery_app.config_from_object(Settings(), namespace="CELERY")


# Define tasks
@celery_app.task(base=CustomTask, bind=True)
def batch_process(self: AbstractTask):

    task_group = []
    for plate_timestep in get_plate_timesteps(self.settings.DATA_DIR):
        task_group.append(
            _construct_timestep_workflow(plate_timestep, self.settings),
        )

    group(task_group).apply_async()


def _construct_timestep_workflow(
    plate_timestep: PlateTimestep,
    settings: Settings,
) -> chain:

    serialized_timestep = plate_timestep.model_dump(mode="json")
    return chain(
        create_archived_timestep.s(
            serialized_timestep,
            str(settings.ARCHIVE_DIR),
        ),
        upload_timestamp.s(),
    )


@celery_app.task(base=CustomTask, bind=True)
def create_archived_timestep(
    self: AbstractTask,
    data: dict,
    archive_dir: str,
    *,
    _filename: str | None = None,
) -> dict:

    plate_data = PlateTimestep.model_validate(data)

    LOGGER.info("Archiving timestep %s", plate_data.experiment_id)

    filename = _filename or f"{uuid4().hex[:6]}.tar"

    archive = self.file_system.make_archive(
        plate_data.raw_img_path, Path(archive_dir) / filename
    )

    archived_timestep = ArchivedPlateTimestep(
        plate_timestep=plate_data,
        archive=Archive(
            path=archive.path,
            checksum=archive.get_checksum(),
        ),
    )

    return archived_timestep.model_dump(mode="json")


@celery_app.task(base=CustomTask, bind=True)
def upload_timestamp(self: AbstractTask, data: dict):
    archived_timestep = ArchivedPlateTimestep.model_validate(data)

    experiment_id = archived_timestep.plate_timestep.experiment_id
    timestamp = archived_timestep.plate_timestep.timestamp.strftime("%Y%m%d_%H%M")

    key = f"raw/{experiment_id}/{timestamp}.tar"
    self.object_storage_client.upload(key, archived_timestep.archive.path)

    LOGGER.info("Uploaded file: %s", key)


# Define signals
@celery_app.on_after_configure.connect
def setup_periodic_task(sender: Celery, **_):
    sender.add_periodic_task(
        crontab(hour=1, minute=0),
        batch_process.s(),
    )


@signals.worker_ready.connect
def on_worker_ready(**_):
    LOGGER.info("Worker ready...")
