"""Celery application."""

from pathlib import Path
from uuid import uuid4

from celery import Celery, signals
from celery.utils.log import get_task_logger
from pydantic import validate_call

from .config import Settings
from .dto import Archive, ArchivedPlateTimestep, PlateTimestep
from .file import FileSystem

LOGGER = get_task_logger(__name__)

celery_app = Celery("worker")

celery_app.config_from_object(Settings(), namespace="CELERY")


# Define tasks
@celery_app.task
@validate_call
def create_archived_timestep(
    data: PlateTimestep,
    archive_dir: Path,
    *,
    _filename: str | None = None,
    _file_system: FileSystem | None = None,
) -> dict:

    filename = _filename or f"{uuid4().hex[:6]}.tar"
    file_system = _file_system or FileSystem()

    archive = file_system.make_archive(data.raw_img_path, archive_dir / filename)

    archived_timestep = ArchivedPlateTimestep(
        plate_timestep=data.timestamp,
        archive=Archive(archive.path, checksum=archive.get_checksum()),
    )

    LOGGER.info("Archiving timestep %s", data.experiment_id)

    return archived_timestep.model_dump(mode="json")


# Define signals
@signals.worker_ready.connect
def on_worker_ready(**_):
    LOGGER.info("Worker ready...")
