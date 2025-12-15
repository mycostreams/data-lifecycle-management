from unittest.mock import AsyncMock

import pytest

from prince_archiver.adapters.file import PathManager, SrcDir
from prince_archiver.adapters.streams import Stream
from prince_archiver.entrypoints.purger.functions import State, delete_src
from prince_archiver.entrypoints.purger.settings import Settings
from prince_archiver.service_layer.dto import NewImagingEvent
from prince_archiver.service_layer.streams import IncomingMessage


@pytest.fixture(name="stream")
def fixture_stream() -> Stream:
    msg = AsyncMock(IncomingMessage)
    msg.processed_data.return_value = AsyncMock(
        NewImagingEvent,
        system="prince",
        local_path="test/path",
        ref_id="test-id",
    )

    async def _stream_range():
        yield msg

    stream = AsyncMock(Stream)
    stream.range.return_value = aiter(_stream_range())

    return stream


async def test_src_dir_deleted(stream: Stream):
    src_dir = AsyncMock(SrcDir)
    src_dir.exists.return_value = True

    path_manager = AsyncMock(PathManager)
    path_manager.get_src_dir.return_value = src_dir

    state = State(
        settings=Settings(
            SRC_DIR="/data",
            SRC_SYSTEMS_DELETE={"prince"},
        ),
        stream=stream,
        path_manager=path_manager,
    )

    await delete_src({"state": state})

    path_manager.get_src_dir.assert_called_once_with("prince", "test/path")
    src_dir.rm.assert_awaited_once_with()


async def test_src_dir_not_deleted(stream: Stream):
    path_manager = AsyncMock(PathManager)
    src_dir = AsyncMock(SrcDir)

    path_manager.get_src_dir.return_value = src_dir
    src_dir.path = "/data/tsu-exp003/test/path"

    state = State(
        settings=Settings(
            SRC_DIR="/data",
            SRC_SYSTEMS_DELETE={"tsu-exp003"},
        ),
        stream=stream,
        path_manager=path_manager,
    )

    await delete_src({"state": state})

    assert path_manager.get_src_dir.call_count == 0
