import asyncio
import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator

from .abc import (
    AbstractArchiver,
    AbstractConfig,
    AbstractManagedArchiver,
    ArchiveEntry,
    ArchiveParams,
)
from .file import ArchiveFileSystem, ExperimentFileSystem, managed_s3_file_system

LOGGER = logging.getLogger(__name__)


@dataclass
class _TargetArchive:
    experiment_id: str
    src_files: list[str]
    target: Path


class Archiver(AbstractArchiver):
    def __init__(
        self,
        experiment_file_system: ExperimentFileSystem,
        archive_file_system: ArchiveFileSystem,
    ):
        self.experiment_file_system = experiment_file_system
        self.archive_file_system = archive_file_system

    async def archive(
        self,
        archive_params: ArchiveParams,
    ) -> list[ArchiveEntry]:
        """Archive all files for a given date for given type.

        Files will be bundled per experiment id.
        """
        LOGGER.info(
            "[%s] Archiving %s/%s",
            archive_params.job_id,
            archive_params.mode,
            archive_params.date,
        )

        archives: list[ArchiveEntry] = []
        async for target_archive in self._get_target_archives(archive_params):
            LOGGER.info(
                "[%s] Creating achive for %s",
                archive_params.job_id,
                target_archive.experiment_id,
            )
            await self._create_archive(target_archive)

            archives.append(
                ArchiveEntry(
                    path=str(target_archive.target),
                    src_keys=target_archive.src_files,
                )
            )

        LOGGER.info("[%s] Archiving complete")

        return archives

    async def _get_target_archives(
        self,
        archive_params: ArchiveParams,
    ) -> AsyncGenerator[_TargetArchive, None]:
        grouped_files = await self.experiment_file_system.list_files_by_date(
            archive_params.date, archive_params.mode
        )
        LOGGER.info("[%s] Count %i", archive_params.job_id, len(grouped_files))

        tar_name = archive_params.date.strftime("%Y-%m-%d.tar")
        for experiment_id, files in grouped_files.items():
            path = Path(archive_params.mode.value, experiment_id, tar_name)
            if not self.archive_file_system.exists(path):
                yield _TargetArchive(
                    experiment_id=experiment_id, target=path, src_files=files
                )

    async def _create_archive(self, target_archive: _TargetArchive):
        with self.archive_file_system.get_temp_dir() as temp_dir:
            src_files = target_archive.src_files

            await self.experiment_file_system.get_files(src_files, temp_dir.path)
            await self.archive_file_system.add(temp_dir, target_archive.target)

            await asyncio.gather(
                *[self.experiment_file_system.tag(file) for file in src_files],
            )


@dataclass
class ArchiverConfig(AbstractConfig):
    bucket_name: str
    base_path: Path


class ManagedArchiver(AbstractManagedArchiver[ArchiverConfig]):
    stack: AsyncExitStack

    async def __aenter__(self) -> Archiver:
        self.stack = await AsyncExitStack().__aenter__()
        s3 = await self.stack.enter_async_context(managed_s3_file_system())

        return Archiver(
            experiment_file_system=ExperimentFileSystem(s3, self.config.bucket_name),
            archive_file_system=ArchiveFileSystem(self.config.base_path),
        )

    async def __aexit__(self, *args):
        await self.stack.aclose()
