import tarfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest

from prince_archiver.file import tar

pytestmark = pytest.mark.integration


@dataclass(kw_only=True)
class _TempDir:
    path: Path
    file_list: set[str]


@pytest.fixture(name="src_tar_dir")
def fixture_src_tar_dir(tmp_path: Path) -> _TempDir:
    src_dir = tmp_path / uuid4().hex[:5]
    src_dir.mkdir()

    file_list = {"./a.txt", "./b.txt"}
    for file_path in (src_dir / file for file in file_list):
        file_path.touch()

    return _TempDir(
        path=src_dir,
        file_list=file_list,
    )


@pytest.fixture(name="image_path")
def fixture_image_path() -> Path:
    return Path(__file__).parent.parent / "data" / "example.tif"


def test_tar(src_tar_dir: _TempDir, tmp_path: Path):
    target_tar = tmp_path / "target.tar"

    tar(src_tar_dir.path, target_tar)

    assert target_tar.exists()
    with tarfile.open(target_tar) as file:
        members = file.getnames()
        assert all(file in members for file in src_tar_dir.file_list)
