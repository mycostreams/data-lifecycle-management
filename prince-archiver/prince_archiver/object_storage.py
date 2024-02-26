import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

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
