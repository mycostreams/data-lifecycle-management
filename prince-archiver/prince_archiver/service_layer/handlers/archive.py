import logging

from prince_archiver.domain.models import ArchiveMember, DataArchiveEntry
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messages import (
    AddDataArchiveEntry,
    ArchivedImagingEvent,
)
from prince_archiver.service_layer.uow import AbstractUnitOfWork

LOGGER = logging.getLogger(__name__)


async def add_data_archive_entry(
    message: AddDataArchiveEntry,
    uow: AbstractUnitOfWork,
):
    async with uow:
        LOGGER.info("[%s] Updating archive entries", message.job_id)

        if await uow.data_archive.get_by_path(message.path):
            raise ServiceLayerException("Already exists.")

        entry = DataArchiveEntry(
            **message.model_dump(exclude={"members"}),
            members=[ArchiveMember(**item.model_dump()) for item in message.members],
        )

        uow.data_archive.add(entry)

        for member in entry.members:
            uow.add_message(
                ArchivedImagingEvent(
                    src_key=member.src_key,
                    data_archive_entry_id=entry.id,
                )
            )

        await uow.commit()
