"""Handlers used to import imaging event into system."""

import logging

from prince_archiver.domain.models import ImagingEvent, SrcDirInfo
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

        imaging_event = ImagingEvent.factory(
            **message.model_dump(exclude={"src_dir_info"}),
            src_dir_info=SrcDirInfo(**message.src_dir_info.model_dump()),
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
