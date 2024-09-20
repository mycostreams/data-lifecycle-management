from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from prince_archiver.adapters.file.file_system import AsyncFileSystem
from prince_archiver.adapters.file.integrations import (
    ArchiveFile,
    EventFile,
    SrcDir,
    SystemDir,
)
from prince_archiver.definitions import System


class MockException(Exception):
    pass


@pytest.fixture(name="system_dir")
def fixture_system_dir():
    file_system = AsyncMock(AsyncFileSystem)
    file_system.list_dir.return_value = (Path("test.json"), Path("test.txt"))

    return SystemDir(
        path=Path("/system"),
        system=System.PRINCE,
        file_system=file_system,
    )


@pytest.fixture(name="src_dir")
def fixture_src_dir():
    return SrcDir(
        path=Path("/src"),
        file_system=AsyncMock(AsyncFileSystem),
    )


@pytest.fixture(name="event_file")
def fixure_event_file(system_dir: SystemDir):
    return EventFile(
        path=Path("/event"),
        system_dir=system_dir,
        file_system=AsyncMock(AsyncFileSystem),
    )


def test_system_dir_events_dir(system_dir: SystemDir):
    assert system_dir.events_dir == Path("/system/events")


async def test_system_dir_iter_events(system_dir: SystemDir):
    events = [event async for event in system_dir.iter_events()]
    assert len(events) == 1

    (event,) = events
    assert event.path == Path("test.json")


@pytest.mark.parametrize(
    "path,is_relative",
    [(Path("/system/is/relative"), True), (Path("/not/relative"), False)],
)
def test_system_dir_is_relative(system_dir: SystemDir, path: Path, is_relative: bool):
    assert system_dir.is_relative(path) == is_relative


async def test_src_dir_copy(src_dir: SrcDir):
    await src_dir.copy(Path("/target"))

    src_dir.file_system.copy_tree.assert_awaited_once_with(
        Path("/src"),
        Path("/target"),
    )


async def test_src_dir_rm(src_dir: SrcDir):
    await src_dir.rm()

    src_dir.file_system.rm_tree.assert_awaited_once_with(Path("/src"))


async def test_src_dir_get_temp_archive(src_dir: SrcDir):
    src_dir.file_system.get_temp_archive.return_value.__aenter__.return_value = Path(
        "/tmp/archive/"
    )

    async with src_dir.get_temp_archive() as archive_file:
        assert isinstance(archive_file, ArchiveFile)


async def test_event_file_removed_on_successful_process(event_file: EventFile):
    async with event_file.process():
        pass

    event_file.file_system.rm.assert_awaited_once_with(Path("/event"))


async def test_event_file_not_removed_on_unsuccessful_process(event_file: EventFile):
    with pytest.raises(MockException):
        async with event_file.process():
            raise MockException

    event_file.file_system.rm.assert_not_awaited()
