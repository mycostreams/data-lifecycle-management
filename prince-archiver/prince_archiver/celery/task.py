from abc import ABC, abstractmethod

import boto3
from celery import Task

from prince_archiver.config import Settings
from prince_archiver.file import AbstractFileSystem, FileSystem
from prince_archiver.object_storage import (
    AbstractObjectStorageClient,
    AWSObjectStorageClient,
)


class AbstractTask(ABC):

    def __init__(
        self,
        *,
        _settings: Settings | None = None,
    ):
        self.settings = _settings or Settings()

    @property
    @abstractmethod
    def object_storage_client(self) -> AbstractObjectStorageClient: ...

    @property
    @abstractmethod
    def file_system(self) -> AbstractFileSystem: ...


class CustomTask(AbstractTask, Task):

    def __init__(
        self,
        *,
        _settings: Settings | None = None,
    ):
        super().__init__(_settings=_settings)
        self._client: AWSObjectStorageClient | None = None
        self._file_system = FileSystem()

    @property
    def object_storage_client(self) -> AWSObjectStorageClient:
        if not self._client:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=self.settings.AWS_ENDPOINT_URL,
            )

            self._client = AWSObjectStorageClient(
                bucket=self.settings.AWS_BUCKET_NAME, s3_client=s3_client
            )

        return self._client

    @property
    def file_system(self):
        return self._file_system
