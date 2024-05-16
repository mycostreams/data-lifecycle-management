import logging
from typing import Callable

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

    def __init__(
        self,
        messagebus_factory: Callable[[], MessageBus],
    ):
        self.messagebus_factory = messagebus_factory

    async def __call__(self, message: AbstractIncomingMessage):
        messagebus = self.messagebus_factory()
        async with message.process():
            data = UpdateArchiveEntries.model_validate_json(message.body)
            LOGGER.info("Archiving job received: %s", data.job_id)

            await messagebus.handle(data)

            LOGGER.info("Archiving job processed: %s", data.job_id)


async def update_data_archive_entries(
    message: UpdateArchiveEntries,
    uow: AbstractUnitOfWork,
):
    async with uow:
        timesteps = await uow.timestamps.get_by_date(message.date)

        mapped_timesteps: dict[str, Timestep] = {}
        for item in timesteps:
            if obj := item.object_store_entry:
                mapped_timesteps[f"{obj.bucket}/{obj.key}"] = item
        persisted_keys = mapped_timesteps.keys()

        for archive in message.archives:
            for key in filter(lambda key: key in persisted_keys, archive.src_keys):
                timestep = mapped_timesteps[key]
                if not timestep.data_archive_entry:
                    LOGGER.info("Timestep already associated to archive %s", key)
                    continue

                LOGGER.info("Adding archive entry for %s", key)
                timestep.data_archive_entry = DataArchiveEntry(
                    job_id=message.job_id,
                    archive_path=archive.path,
                    file=key,
                )

        await uow.commit()


class DeletedExpiredUploadsHandler(AbstractHandler[DeleteExpiredUploads]):

    def __init__(
        self,
        s3: S3FileSystem,
    ):
        self.s3 = s3

    async def __call__(self, message: DeleteExpiredUploads, uow: AbstractUnitOfWork):
        async with uow:
            expiring_timestamps = filter(
                self._is_deletable,
                await uow.timestamps.get_by_upload_date(message.uploaded_on),
            )

            remote_paths: list[str] = []
            for item in expiring_timestamps:
                object_store_entry = item.object_store_entry
                assert object_store_entry

                object_store_entry.deletion_event = DeletionEvent(job_id=message.job_id)
                remote_paths.append(self._get_remote_path(object_store_entry))

            await self.s3._bulk_delete(remote_paths)
            await uow.commit()

    @staticmethod
    def _is_deletable(timestamp: Timestep) -> bool:
        object_store_entry = timestamp.object_store_entry

        check = bool(
            object_store_entry
            and not object_store_entry.deletion_event
            and timestamp.data_archive_entry
        )

        if not check:
            LOGGER.info("Cannot delete object store entry %s", timestamp.timestep_id)

        return check

    @staticmethod
    def _get_remote_path(object_store_entry: ObjectStoreEntry) -> str:
        return f"{object_store_entry.bucket}/{object_store_entry.key}"
