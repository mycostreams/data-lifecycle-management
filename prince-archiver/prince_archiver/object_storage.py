import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import s3fs

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


LOGGER = logging.getLogger(__name__)


class AbstractObjectStorageClient(ABC):

    @abstractmethod
    def upload(self, key: str, path: Path): ...


class ObjectStorageClient(AbstractObjectStorageClient):

    def __init__(
        self,
        bucket: str,
        s3_client: "S3Client",
    ):
        self.bucket = bucket
        self.s3_client = s3_client

    def upload(self, key: str, path: Path):
        self.s3_client.upload_file(
            Filename=path.as_posix(),
            Key=key,
            Bucket=self.bucket,
        )


async def upload_to_s3(source: Path):

    s3 = s3fs.S3FileSystem(asynchronous=True)
    session = await s3.set_session()

    await s3._put_file(
        source,
        f"mycostreams-dev/{source.name}",
        max_concurrency=8,
    )

    await session.close()
