"""Handlers used to export imaging event bundles."""

import logging

from prince_archiver.domain.models import EventArchive, ObjectStoreEntry
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.service_layer import messages
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.uow import AbstractUnitOfWork

LOGGER = logging.getLogger(__name__)


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
