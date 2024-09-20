from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from prince_archiver.adapters.file import ArchiveFile, ArchiveInfo, PathManager, SrcDir
from prince_archiver.domain.models import ImagingEvent
from prince_archiver.domain.value_objects import Checksum

from .utils import MockImagingEventRepo, MockUnitOfWork


@pytest.fixture(name="uow")
def fixture_uow(
    exported_imaging_event: ImagingEvent,
    unexported_imaging_event: ImagingEvent,
):
    return MockUnitOfWork(
        imaging_event_repo=MockImagingEventRepo(
            imaging_events=[exported_imaging_event, unexported_imaging_event],
        ),
    )


@pytest.fixture()
def mock_path_manager() -> PathManager:
    mock_archive_file = AsyncMock(ArchiveFile, path=Path("/test"))
    mock_archive_file.get_info.return_value = ArchiveInfo(
        checksum=Checksum(hex="test"),
        size=1024,
    )

    mock_src_dir = AsyncMock(SrcDir)
    mock_src_dir.get_temp_archive.return_value.__aenter__.return_value = (
        mock_archive_file
    )

    mock_path_manager = AsyncMock(PathManager)
    mock_path_manager.get_src_dir.return_value = mock_src_dir

    return mock_path_manager
