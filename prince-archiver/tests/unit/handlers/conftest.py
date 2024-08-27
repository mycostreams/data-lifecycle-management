from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from prince_archiver.adapters.file import ArchiveFileManager
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
def mock_file_manager() -> ArchiveFileManager:
    mock_file_manager = AsyncMock(ArchiveFileManager)

    mock_file_manager.get_archive_checksum.return_value = Checksum(hex="test")
    mock_file_manager.get_archive_size.return_value = 1024
    mock_file_manager.get_temp_archive.return_value.__aenter__ = AsyncMock(
        return_value=Path("test")
    )
    mock_file_manager.get_file_count.return_value = 5
    mock_file_manager.get_raw_metadata.return_value = {"test_key": "test_value"}

    return mock_file_manager
