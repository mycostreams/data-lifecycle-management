"""Handlers used to export imaging event bundles."""

import asyncio
import logging
from typing import Callable

import s3fs
from arq import ArqRedis

from prince_archiver.adapters.file import ArchiveFileManager
from prince_archiver.domain.models import EventArchive, ObjectStoreEntry
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.service_layer import messages
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.uow import AbstractUnitOfWork

LOGGER = logging.getLogger(__name__)


class ExportHandler:
    """
    Class handles export of local images to cloud.
    """

    def __init__(
        self,
        redis: ArqRedis,
        s3: s3fs.S3FileSystem,
        key_generator: Callable[[messages.ExportImagingEvent], str],
        file_manager: ArchiveFileManager | None = None,
    ):
        self.s3 = s3
        self.redis = redis
        self.file_manager = file_manager or ArchiveFileManager()
        self.key_generator = key_generator

    async def __call__(
        self,
        message: messages.ExportImagingEvent,
    ):
        LOGGER.info("[%s] Exporting", message.ref_id)

        key = self.key_generator(message)
        src_dir = self.file_manager.get_src_path(message.local_path)
        async with (
            self.file_manager.get_temp_archive(src_dir) as archive_path,
            asyncio.TaskGroup() as tg,
        ):
            checksum_task = tg.create_task(
                self.file_manager.get_archive_checksum(archive_path),
            )
            size_task = tg.create_task(
                self.file_manager.get_archive_size(archive_path),
            )
            tg.create_task(self.s3._put_file(archive_path, key))

        msg = messages.ExportedImagingEvent(
            ref_id=message.ref_id,
            checksum=checksum_task.result().__dict__,
            size=size_task.result(),
            key=key,
        )

        await self.redis.enqueue_job(
            "run_persist_export",
            msg.model_dump(mode="json"),
            _queue_name="arq:queue-cron",
        )


async def persist_imaging_event_export(
    message: messages.ExportedImagingEvent,
    uow: AbstractUnitOfWork,
):
    """
    Persist imaging event export.
    """
    LOGGER.info("[%s] Persisting export", message.ref_id)

    async with uow:
        imaging_event = await uow.imaging_events.get_by_ref_id(message.ref_id)
        if not imaging_event:
            raise ServiceLayerException("Rejecting persistence")

        imaging_event.add_event_archive(
            EventArchive(
                size=message.size,
                checksum=Checksum(**message.checksum.model_dump()),
            )
        )

        imaging_event.add_object_store_entry(
            ObjectStoreEntry(
                key=message.key,
                uploaded_at=message.timestamp,
            )
        )
        await uow.commit()
