import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import s3fs

from .config import AWSSettings

LOGGER = logging.getLogger(__name__)


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
