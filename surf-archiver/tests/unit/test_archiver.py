from datetime import date
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from surf_archiver.archiver import ArchiveEntry, ArchiveParams, Archiver
from surf_archiver.definitions import Mode
from surf_archiver.file import ArchiveFileSystem, ExperimentFileSystem


@pytest.fixture(name="experiment_file_system")
def fixture_experiment_file_system() -> ExperimentFileSystem:
    file_system = AsyncMock(ExperimentFileSystem)
    file_system.list_files_by_date.return_value = {
        "test-id": ["test-bucket/images/test-id/20000101_0000.tar"],
    }
    return file_system


@pytest.fixture(name="archive_params")
def fixture_archive_params() -> ArchiveParams:
    return ArchiveParams(
        date=date(2000, 1, 1),
        mode=Mode.STITCH,
        job_id=UUID("e889038f94224655b7374162d5e9a909"),
    )


async def test_new_files_are_archived(
    archive_params: ArchiveParams, experiment_file_system: ExperimentFileSystem
):
    archive_file_system = AsyncMock(ArchiveFileSystem)
    archive_file_system.exists.return_value = False

    archiver = Archiver(experiment_file_system, archive_file_system)

    expected = [
        ArchiveEntry(
            path="images/test-id/2000-01-01.tar",
            src_keys=["test-bucket/images/test-id/20000101_0000.tar"],
        )
    ]

    archives = await archiver.archive(archive_params)

    assert archives == expected


async def test_already_archived_files_are_skipped(
    archive_params: ArchiveParams,
    experiment_file_system: ExperimentFileSystem,
):
    archive_file_system = AsyncMock(ArchiveFileSystem)
    archive_file_system.exists.return_value = True

    archiver = Archiver(experiment_file_system, archive_file_system)

    archives = await archiver.archive(archive_params)
    assert not archives
