"""Handlers used to export imaging event bundles."""

import asyncio
import logging
from dataclasses import asdict
from typing import Callable

import s3fs
from arq import ArqRedis

from prince_archiver.adapters.file import PathManager
from prince_archiver.definitions import SrcDirKey
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
        path_manager: PathManager,
    ):
        self.s3 = s3
        self.redis = redis
        self.key_generator = key_generator
        self.path_manager = path_manager

    async def __call__(
        self,
        message: messages.ExportImagingEvent,
    ):
        LOGGER.info("[%s] Exporting", message.ref_id)

        key = self.key_generator(message)

        src_dir = self.path_manager.get_src_dir(
            SrcDirKey.STAGING if message.staging_path else message.system,
            message.staging_path or message.local_path,
        )
        async with (
            src_dir.get_temp_archive() as archive_file,
            asyncio.TaskGroup() as tg,
        ):
            t1 = tg.create_task(archive_file.get_info())
            tg.create_task(self.s3._put_file(archive_file.path, key))

        msg = messages.ExportedImagingEvent(
            ref_id=message.ref_id,
            key=key,
            **asdict(t1.result()),
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
