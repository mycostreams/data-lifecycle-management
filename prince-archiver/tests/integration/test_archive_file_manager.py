import json
import tarfile
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from prince_archiver.adapters.file import (
    ArchiveFileManager,
    ArchivePath,
    SrcPath,
)
from prince_archiver.definitions import Algorithm
from prince_archiver.domain.value_objects import Checksum

pytestmark = pytest.mark.integration


@pytest.fixture(name="archive_file_manager")
def fixture_archive_file_manager() -> ArchiveFileManager:
    return ArchiveFileManager()


@pytest.fixture(name="src_dir")
def fixture_src_dir(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (src_dir / "test.txt").touch()

    return SrcPath(src_dir)


@pytest.fixture(name="temp_file")
def fixture_temp_file(tmp_path: Path) -> Path:
    return tmp_path / uuid4().hex[:6]


async def test_file_count(
    archive_file_manager: ArchiveFileManager,
    src_dir: SrcPath,
):
    file_count = await archive_file_manager.get_file_count(src_dir)
    assert file_count == 1


async def test_get_temp_archive(
    archive_file_manager: ArchiveFileManager,
    src_dir: SrcPath,
):
    async with archive_file_manager.get_temp_archive(src_dir) as temp_archive:
        assert temp_archive.exists()

        with tarfile.open(temp_archive, "r") as tar:
            assert set(tar.getnames()) == {".", "./test.txt"}

    # check that it has been deleted
    assert not temp_archive.exists()


async def test_get_checksum(
    archive_file_manager: ArchiveFileManager,
    temp_file: Path,
):
    contents = b"123"
    temp_file.write_bytes(contents)

    checksum = await archive_file_manager.get_archive_checksum(ArchivePath(temp_file))

    expected = Checksum(
        algorithm=Algorithm.SHA256,
        hex=sha256(contents).hexdigest(),
    )

    assert checksum == expected


async def test_get_size(
    archive_file_manager: ArchiveFileManager,
    temp_file: Path,
):
    temp_file.write_bytes(b"123")

    size = await archive_file_manager.get_archive_size(ArchivePath(temp_file))

    assert size == temp_file.stat().st_size


async def test_exists(
    archive_file_manager: ArchiveFileManager,
    temp_file: Path,
):
    # Test non existent file
    assert not await archive_file_manager.exists(temp_file)

    # # test existent file
    temp_file.touch()
    assert await archive_file_manager.exists(temp_file)


async def test_get_raw_metadata_valid_json(
    archive_file_manager: ArchiveFileManager,
    temp_file: Path,
):
    src_data = {"key": "value"}
    temp_file.write_text(json.dumps(src_data))

    out_data = await archive_file_manager.get_raw_metadata(
        SrcPath(temp_file.parent),
        filename=temp_file.name,
    )

    assert src_data == out_data


async def test_get_raw_metadata_file_missing(
    archive_file_manager: ArchiveFileManager,
    temp_file: Path,
):
    out_data = await archive_file_manager.get_raw_metadata(
        SrcPath(temp_file.parent),
        filename=temp_file.name,
    )

    assert out_data == {}
