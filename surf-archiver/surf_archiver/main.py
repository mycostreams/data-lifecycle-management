import logging
from contextlib import AsyncExitStack
from uuid import UUID

from .archiver import AbstractManagedArchiver, ArchiveEntry, ArchiveParams
from .publisher import AbstractManagedPublisher, BaseMessage
from .utils import DateT

LOGGER = logging.getLogger(__name__)


class Payload(BaseMessage):
    job_id: UUID
    date: DateT
    archives: list[ArchiveEntry]


async def run_archiving(
    archive_params: ArchiveParams,
    managed_achviver: AbstractManagedArchiver,
    managed_publisher: AbstractManagedPublisher,
):
    async with AsyncExitStack() as stack:
        archiver = await stack.enter_async_context(managed_achviver)
        publisher = await stack.enter_async_context(managed_publisher)

        archives = await archiver.archive(archive_params)

        payload = Payload(
            job_id=archive_params.job_id,
            date=archive_params.date,
            archives=archives,
        )
        await publisher.publish(payload)
