import logging

from .archiver import AbstractManagedArchiver, ArchiveParams

LOGGER = logging.getLogger(__name__)


async def run_archiving(
    archive_params: ArchiveParams,
    managed_archiver: AbstractManagedArchiver,
):
    async with managed_archiver as archiver:
        await archiver.archive(archive_params)
