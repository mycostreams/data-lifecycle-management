"""Celery application."""

import asyncio
import shutil
import tarfile

import cv2
import s3fs
from celery import shared_task
from celery.utils.log import get_task_logger

from .base_task import AbstractTask, ConcreteTask

LOGGER = get_task_logger(__name__)


@shared_task(base=ConcreteTask, bind=True)
def compress_image(self: AbstractTask, source: str, target: str):
    """Compress an input image using LZW compression."""
    source_path = self.settings.DATA_DIR / source

    target_path = self.settings.TEMP_FILE_DIR / target
    target_path.parent.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(source_path))

    cv2.imwrite(
        str(target_path),
        img,
        params=(cv2.IMWRITE_TIFF_COMPRESSION, 5),
    )


@shared_task(base=ConcreteTask, bind=True)
def archive_images(self: AbstractTask, source: str, target: str):
    """Save input as tar file."""
    source_path = self.settings.TEMP_FILE_DIR / source

    target_path = self.settings.ARCHIVE_DIR / target
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(target_path, "w") as tar:
        tar.add(source_path, arcname=".")

    # Remove the temporary files
    shutil.rmtree(source_path)


@shared_task(base=ConcreteTask, bind=True)
def make_thumbnail(source: str, target: str, scale_factor: float = 0.25):
    """Make a thumbnail image."""
    img = cv2.imread(source)
    resized_img = cv2.resize(
        img,
        (0, 0),
        fx=scale_factor,
        fy=scale_factor,
    )

    cv2.imwrite(target, resized_img)


@shared_task(base=ConcreteTask, bind=True)
def upload_to_s3(self: AbstractTask, source: str, target: str):
    async def _upload_to_s3():
        s3 = s3fs.S3FileSystem(
            key=self.settings.AWS_SECRET_ACCESS_KEY,
            secret=self.settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=self.settings.AWS_ENDPOINT_URL,
            asynchronous=True,
        )

        session = await s3.set_session()

        await s3._put_file(
            source,
            f"{self.settings.AWS_BUCKET_NAME}/{target}",
            max_concurrency=8,
        )

        await session.close()

    asyncio.run(_upload_to_s3())
