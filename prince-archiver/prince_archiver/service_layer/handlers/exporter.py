"""Handlers used to export imaging event bundles."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from uuid import uuid4

import s3fs

from prince_archiver.adapters.file import ArchiveFileManager, SrcPath
from prince_archiver.definitions import EventType
from prince_archiver.domain.models import EventArchive, ImagingEvent, ObjectStoreEntry
from prince_archiver.service_layer import messages
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messagebus import AbstractHandler
from prince_archiver.service_layer.uow import AbstractUnitOfWork

LOGGER = logging.getLogger(__name__)


def key_generator(bucket: str, imaging_event: ImagingEvent) -> str:
    date_folder = imaging_event.timestamp.strftime("%Y%m%d")
    file_name = imaging_event.timestamp.strftime("%H%M%S.tar")
    type_ = "images" if imaging_event.type == EventType.STITCH else "videos"

    return f"{bucket}/{type_}/{imaging_event.experiment_id}/{date_folder}/{file_name}"


@dataclass
class Context:
    base_path: Path
    key_generator: Callable[[ImagingEvent], str]


async def initiate_imaging_event_export(
    message: messages.InitiateExportEvent,
    uow: AbstractUnitOfWork,
    *,
    context: Context,
):
    """
    Initiate the export of an image timestep.
    """

    LOGGER.info("[%s] Initiating export", message.ref_id)

    async with uow:
        imaging_event = await uow.imaging_events.get_by_ref_id(message.ref_id)
        if not imaging_event or imaging_event.event_archive:
            raise ServiceLayerException("Rejecting export")

        uow.add_message(
            messages.ExportImagingEvent(
                ref_id=imaging_event.ref_id,
                type=imaging_event.type,
                local_path=context.base_path / imaging_event.local_path,
                target_key=context.key_generator(imaging_event),
            )
        )


class ExportHandler(AbstractHandler[messages.ExportImagingEvent]):
    """
    Class handles export of local images to cloud.
    """

    def __init__(
        self,
        s3: s3fs.S3FileSystem,
        file_manager: ArchiveFileManager | None = None,
    ):
        self.s3 = s3
        self.file_manager = file_manager or ArchiveFileManager()

    async def __call__(
        self,
        message: messages.ExportImagingEvent,
        uow: AbstractUnitOfWork,
    ):
        LOGGER.info("[%s] Exporting", message.ref_id)

        async with uow:
            src_dir = SrcPath(message.local_path)
            async with (
                self.file_manager.get_temp_archive(src_dir) as archive_path,
                asyncio.TaskGroup() as tg,
            ):
                checksum_task = tg.create_task(
                    self.file_manager.get_archive_checksum(archive_path),
                )

                file_count_task = tg.create_task(
                    self.file_manager.get_file_count(src_dir),
                )

                size_task = tg.create_task(
                    self.file_manager.get_archive_size(archive_path),
                )

                tg.create_task(
                    self.s3._put_file(archive_path, message.target_key),
                )

            uow.add_message(
                messages.ExportedImagingEvent(
                    ref_id=message.ref_id,
                    checksum=checksum_task.result(),
                    img_count=file_count_task.result(),
                    size=size_task.result(),
                    key=message.target_key,
                )
            )
            await uow.commit()


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
                id=uuid4(),
                size=message.size,
                img_count=message.img_count,
                checksum=message.checksum,
            )
        )

        imaging_event.add_object_store_entry(
            ObjectStoreEntry(
                key=message.key,
                uploaded_at=message.timestamp,
            )
        )
        await uow.commit()
