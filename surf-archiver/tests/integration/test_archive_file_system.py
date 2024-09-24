from pathlib import Path
from tarfile import TarFile
from typing import Callable
from uuid import uuid4

import pytest

from surf_archiver.file import ArchiveFileSystem, _TempDir

FactoryT = Callable[[], Path]


@pytest.fixture(name="dir_factory")
def fixture_dir_factory(tmp_path: Path) -> FactoryT:
    def _dir_factory() -> Path:
        dir_ = tmp_path / uuid4().hex
        dir_.mkdir()
        return dir_

    return _dir_factory


@pytest.fixture(name="archive_file_system")
def fixture_archive_file_system(dir_factory: FactoryT) -> ArchiveFileSystem:
    return ArchiveFileSystem(dir_factory())


@pytest.fixture(name="populated_temp_dir")
def fixture_populated_temp_dir(dir_factory: FactoryT) -> _TempDir:
    dir_ = dir_factory()

    file = dir_ / "test.txt"
    file.touch()

    return _TempDir(dir_)


def test_file_exists(archive_file_system: ArchiveFileSystem):
    file_name = Path(uuid4().hex)
    (archive_file_system.base_path / file_name).touch()

    assert archive_file_system.exists(file_name)


def test_file_does_not_exist(archive_file_system: ArchiveFileSystem):
    file_name = Path(uuid4().hex)
    assert not archive_file_system.exists(file_name)


async def test_add_temp_directory_to_file_system(
    archive_file_system: ArchiveFileSystem,
    populated_temp_dir: _TempDir,
):
    await archive_file_system.add(populated_temp_dir, Path("test.tar"))

    expected_target = archive_file_system.base_path / "test.tar"

    assert expected_target.exists()
    with TarFile(expected_target, "r") as tarfile:
        assert tarfile.getnames() == [".", "./test.txt"]


def test_get_temp_dir():
    with ArchiveFileSystem.get_temp_dir() as tmp_dir:
        assert tmp_dir.path.exists()

    assert not tmp_dir.path.exists()
