"""Celery application."""

from pathlib import Path

from celery import Celery, signals
from celery.utils.log import get_task_logger
from pydantic import validate_call
from pathlib import Path

from .config import Settings
from .dto import PlateTimestep
from .file import archive_plate_timestep

LOGGER = get_task_logger(__name__)


celery_app = Celery("worker")

celery_app.config_from_object(Settings(), namespace="CELERY")


# Define tasks
@celery_app.task
@validate_call
def create_archived_timestep(data: PlateTimestep, archive_dir: Path) -> dict:
    """Convert archive to dict."""

    LOGGER.info("Archiving timestep %s", data.experiment_id)

    archive = archive_plate_timestep(
        plate_timestep=data,
        target_dir=archive_dir,
    )

    return archive.model_dump(mode="json")


# Define signals
@signals.worker_ready.connect
def on_worker_ready(**_):
    LOGGER.info("Worker ready...")

