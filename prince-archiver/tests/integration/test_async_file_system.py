import json
import tarfile
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from prince_archiver.adapters.file.checksum import ChecksumFactory
from prince_archiver.adapters.file.file_system import AsyncFileSystem

pytestmark = pytest.mark.integration


@pytest.fixture(name="file_system")
def fixture_file_system() -> AsyncFileSystem:
    return AsyncFileSystem()


@pytest.fixture(name="src_dir")
def fixture_src_dir(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    return src_dir


@pytest.fixture(name="src_file_path")
def fixture_src_file_path(src_dir: Path):
    src_path = src_dir / "test.json"
    src_path.write_bytes(b'{"a": 1}')
    return src_path


async def test_get_checksum():
    async def mock_iterator():
        for item in (b"test",):
            yield item

    checksum = await ChecksumFactory.get_checksum(mock_iterator())

    assert checksum.hex == sha256(b"test").hexdigest()


async def test_copy_tree(
    file_system: AsyncFileSystem,
    src_dir: Path,
    tmp_path: Path,
):
    target = tmp_path / uuid4().hex
    await file_system.copy_tree(src_dir, target)

    assert target.exists()


async def test_rm_tree(
    file_system: AsyncFileSystem,
    src_dir: Path,
):
    await file_system.rm_tree(src_dir)

    assert not src_dir.exists()


async def test_rm(
    file_system: AsyncFileSystem,
    src_file_path: Path,
):
    await file_system.rm(src_file_path)

    assert not src_file_path.exists()


async def test_iter_bytes(
    file_system: AsyncFileSystem,
    src_file_path: Path,
):
    assert await anext(file_system.iter_bytes(src_file_path, None)) == b'{"a": 1}'


async def test_read_json(
    file_system: AsyncFileSystem,
    src_file_path: Path,
):
    assert await file_system.read_json(src_file_path, mapper=json.loads) == {"a": 1}


async def test_list_dir(
    file_system: AsyncFileSystem,
    src_file_path: Path,
):
    file_list = await file_system.list_dir(src_file_path.parent)
    assert file_list == [src_file_path]


async def test_tar_tree(
    file_system: AsyncFileSystem,
    src_file_path: Path,
    tmp_path: Path,
):
    target_path = tmp_path / uuid4().hex
    await file_system.tar_tree(src_file_path.parent, target_path)

    assert target_path.exists()

    with tarfile.open(target_path, "r") as tar:
        assert set(tar.getnames()) == {".", "./test.json"}


async def test_get_size(
    file_system: AsyncFileSystem,
    src_file_path: Path,
):
    assert await file_system.get_size(src_file_path) == src_file_path.stat().st_size


async def test_get_temp_archive(
    file_system: AsyncFileSystem,
    src_dir: Path,
):
    async with file_system.get_temp_archive(src_dir) as target_path:
        assert target_path.exists()

    assert not target_path.exists()


async def test_exists(file_system: AsyncFileSystem, src_file_path: Path):
    assert await file_system.exists(src_file_path)
    assert not await file_system.exists(src_file_path.parent / uuid4().hex)
