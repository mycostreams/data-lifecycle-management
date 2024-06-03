import logging
from functools import partial
from typing import Callable
from uuid import UUID
from asyncio import Semaphore, TaskGroup

from aio_pika.abc import AbstractIncomingMessage
from s3fs import S3FileSystem

from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.messagebus import AbstractHandler, MessageBus
from prince_archiver.models import (
    DataArchiveEntry,
    DeletionEvent,
    ObjectStoreEntry,
    Timestep,
)

from .dto import DeleteExpiredUploads, UpdateArchiveEntries

LOGGER = logging.getLogger(__name__)


class SubscriberMessageHandler:

    DTO_CLASS = UpdateArchiveEntries

    def __init__(
        self,
        messagebus_factory: Callable[[], MessageBus],
    ):
        self.messagebus_factory = messagebus_factory

    async def __call__(self, message: AbstractIncomingMessage):
        async with message.process():
            try:
                await self._process(message.body)
            except Exception as err:
                LOGGER.exception(err)
                raise err

    async def _process(self, raw_message: bytes):
        messagebus = self.messagebus_factory()
        message = self.DTO_CLASS.model_validate_json(raw_message)

        await messagebus.handle(message)


async def update_data_archive_entries(
    message: UpdateArchiveEntries,
    uow: AbstractUnitOfWork,
):
    async with uow:
        LOGGER.info("[%s] Updating archive entries", message.job_id)

        timesteps = await uow.timestamps.get_by_date(message.date)

        mapped_timesteps: dict[str, Timestep] = {}
        for item in timesteps:
            if obj := item.object_store_entry:
                mapped_timesteps[f"{obj.bucket}/{obj.key}"] = item
        persisted_keys = mapped_timesteps.keys()

        for archive in message.archives:
            for key in filter(lambda key: key in persisted_keys, archive.src_keys):
                timestep = mapped_timesteps[key]
                if timestep.data_archive_entry:
                    msg = "[%s] Timestep already associated to archive %s"
                    LOGGER.info(msg, message.job_id, key)
                    continue

                timestep.data_archive_entry = DataArchiveEntry(
                    job_id=message.job_id,
                    archive_path=archive.path,
                    file=key,
                )

        await uow.commit()


class DeletedExpiredUploadsHandler(AbstractHandler[DeleteExpiredUploads]):

    CONCURRENT_DELETIONS = 5
    DELETE_CHUNK_SIZE = 50

    def __init__(self, s3: S3FileSystem, *, sem: Semaphore | None = None):
        self.s3 = s3
        self.sem = sem or Semaphore(self.CONCURRENT_DELETIONS)

    async def __call__(self, message: DeleteExpiredUploads, uow: AbstractUnitOfWork):
        async with uow:
            msg = "[%s] Deleting expired uploads for %s"
            LOGGER.info(msg, message.job_id, message.uploaded_on)

            expiring_timestamps = filter(
                partial(self._is_deletable, job_id=message.job_id),
                await uow.timestamps.get_by_upload_date(message.uploaded_on),
            )

            remote_paths: list[str] = []
            for item in expiring_timestamps:
                object_store_entry = item.object_store_entry
                assert object_store_entry

                object_store_entry.deletion_event = DeletionEvent(job_id=message.job_id)
                remote_paths.append(self._get_remote_path(object_store_entry))

            await self._bulk_delete(remote_paths)
            await uow.commit()

            LOGGER.info("[%s] Deleted %i entires", message.job_id, len(remote_paths))

    async def _bulk_delete(self, keys: list[str]):
        async with TaskGroup() as tasks:
            for index in range(0, len(keys), self.DELETE_CHUNK_SIZE):
                chunk = keys[index : index + self.DELETE_CHUNK_SIZE]
                tasks.create_task(self._delete_chunk(chunk))

    async def _delete_chunk(self, keys: list[str]):
        async with self.sem:
            await self.s3._bulk_delete(keys)

    @staticmethod
    def _is_deletable(timestamp: Timestep, *, job_id: UUID | None = None) -> bool:
        object_store_entry = timestamp.object_store_entry

        is_deleted = bool(object_store_entry and object_store_entry.deletion_event)
        is_archived = bool(timestamp.data_archive_entry)

        check = is_archived and not is_deleted
        if not check:
            msg = "[%s] Skipping %s: Archived- %s/ Deleted- %s"
            LOGGER.info(msg, job_id, timestamp.timestep_id, is_archived, is_deleted)

        return check

    @staticmethod
    def _get_remote_path(object_store_entry: ObjectStoreEntry) -> str:
        return f"{object_store_entry.bucket}/{object_store_entry.key}"
