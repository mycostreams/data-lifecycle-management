"""Handlers used to import imaging event into system."""

import logging

from prince_archiver.domain import models
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.service_layer import messages
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.uow import AbstractUnitOfWork

LOGGER = logging.getLogger(__name__)


async def import_imaging_event(
    message: messages.ImportImagingEvent,
    uow: AbstractUnitOfWork,
):
    LOGGER.info("[%s] Importing imaging event", message.ref_id)

    async with uow:
        if await uow.imaging_events.get_by_ref_id(message.ref_id):
            raise ServiceLayerException("Already imported.")

        imaging_event = models.ImagingEvent.factory(
            **message.model_dump(exclude={"src_dir_info"}),
            src_dir_info=models.SrcDirInfo(**message.src_dir_info.model_dump()),
        )

        uow.imaging_events.add(imaging_event)

        uow.add_message(
            messages.ImportedImagingEvent(
                id=imaging_event.id,
                **message.model_dump(),
            ),
        )

        await uow.commit()

    LOGGER.info("[%s] Imported imaging event", message.ref_id)


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
            models.EventArchive(
                size=message.size,
                checksum=Checksum(**message.checksum.model_dump()),
            )
        )

        imaging_event.add_object_store_entry(
            models.ObjectStoreEntry(
                key=message.key,
                uploaded_at=message.timestamp,
            )
        )
        await uow.commit()


async def add_data_archive_entry(
    message: messages.AddDataArchiveEntry,
    uow: AbstractUnitOfWork,
):
    LOGGER.info("[%s] Updating archive entries %s", message.job_id, message.path)

    async with uow:
        if await uow.data_archive.get_by_path(message.path):
            raise ServiceLayerException("Already exists.")

        entry = models.DataArchiveEntry(
            **message.model_dump(exclude={"members"}),
            members=[
                models.ArchiveMember(**item.model_dump()) for item in message.members
            ],
        )

        uow.data_archive.add(entry)

        for member in entry.members:
            uow.add_message(
                messages.ArchivedImagingEvent(
                    src_key=member.src_key,
                    data_archive_entry_id=entry.id,
                )
            )

        await uow.commit()
