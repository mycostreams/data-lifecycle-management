import logging
import tarfile
from contextlib import asynccontextmanager
from enum import IntEnum
from pathlib import Path
from typing import AsyncGenerator

import cv2
import s3fs

from .config import AWSSettings

LOGGER = logging.getLogger(__name__)


class Compression(IntEnum):

    DEFLATE = 8
    LZW = 5


def compress(src: Path, target: Path, mode: Compression = Compression.DEFLATE):
    LOGGER.debug("Compressing %s", src)

    img = cv2.imread(str(src))
    cv2.imwrite(
        str(target),
        img,
        params=(cv2.IMWRITE_TIFF_COMPRESSION, mode),
    )

    LOGGER.debug("Compressed %s", src)


def tar(src: Path, target: Path):
    LOGGER.debug("Tarring %s", src)

    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(target, "a") as tar:
        tar.add(src, arcname=".")

    LOGGER.debug("Tarred %s", src)


@asynccontextmanager
async def managed_file_system(
    settings: AWSSettings,
) -> AsyncGenerator[s3fs.S3FileSystem, None]:
    client_kwargs = {}
    if settings.AWS_REGION_NAME:
        client_kwargs["region_name"] = settings.AWS_REGION_NAME

    s3 = s3fs.S3FileSystem(
        key=settings.AWS_ACCESS_KEY_ID,
        secret=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        client_kwargs=client_kwargs,
        asynchronous=True,
        max_concurrency=settings.UPLOAD_MAX_CONCURRENCY,
    )

    session = await s3.set_session()

    yield s3

    await session.close()
