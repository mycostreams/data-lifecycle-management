from contextlib import asynccontextmanager
from typing import AsyncGenerator, Protocol

from s3fs import S3FileSystem


class AWSSettings(Protocol):
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_ENDPOINT_URL: str | None
    AWS_REGION_NAME: str | None
    UPLOAD_MAX_CONCURRENCY: int


def file_system_factory(settings: AWSSettings) -> S3FileSystem:
    client_kwargs = {}
    if settings.AWS_REGION_NAME:
        client_kwargs["region_name"] = settings.AWS_REGION_NAME

    return S3FileSystem(
        key=settings.AWS_ACCESS_KEY_ID,
        secret=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        client_kwargs=client_kwargs,
        asynchronous=True,
        max_concurrency=settings.UPLOAD_MAX_CONCURRENCY,
    )


@asynccontextmanager
async def managed_file_system(
    file_system: S3FileSystem,
) -> AsyncGenerator[S3FileSystem, None]:
    session = await file_system.set_session()

    yield file_system

    await session.close()
