"""Celery application."""

import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

from celery import shared_task
from celery.utils.log import get_task_logger

from prince_archiver.dto import TimestepDTO

from .base_task import AbstractTask, ConcreteTask

LOGGER = get_task_logger(__name__)


@shared_task(base=ConcreteTask, bind=True)
def archive_timestep(self: AbstractTask, data: dict):
    input_data = TimestepDTO.model_validate(data)

    LOGGER.info("Archiving %s", input_data.key)

    with (
        TemporaryDirectory() as temp_dir,
        tarfile.open(input_data.experiment_archive_path, "a") as tar,
    ):
        timestep_archive = Path(temp_dir) / input_data.archive_name

        file = self.file_system.make_archive(input_data.raw_img_path, timestep_archive)

        tar.add(file.path, arcname=input_data.archive_name)

    LOGGER.info("Archived %s", input_data.key)


@shared_task(base=ConcreteTask, bind=True)
def upload_to_object_store(self: AbstractTask, data: dict):

    input_data = TimestepDTO.model_validate(data)

    LOGGER.info("Uploading %s to s3.", input_data.key)

    with (
        TemporaryDirectory() as temp_dir,
        tarfile.open(input_data.experiment_archive_path, "r") as tar,
    ):
        tar.extract(input_data.archive_name, temp_dir)
        self.object_storage_client.upload(
            input_data.key,
            Path(temp_dir) / input_data.archive_name,
        )

    LOGGER.info("Uploaded %s to s3", input_data.key)
