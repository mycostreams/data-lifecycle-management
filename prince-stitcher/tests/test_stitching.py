import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from image_stitcher.stitcher import Params, Stitcher


@pytest.fixture(name="params")
def fixture_params() -> Params:
    """Fixture defining the defaults for stitcher.

    Within test directory a 4x4 image has been provided.

    """
    return Params(
        grid_size_x=2,
        grid_size_y=2,
    )


@pytest.fixture(name="data_dir")
def fixture_data_dir(tmp_path: Path) -> Path:
    """Fixture defining directory containing source images.

    Note: we copy the test data into a temp directory as the ImageJ
    plugin will add files to this directory. The temp directory ensures
    that things get cleaned up.

    """
    src_dir = Path(__file__).parent / "data" / "img"
    data_dir = tmp_path / "img"

    shutil.copytree(src_dir, data_dir)

    return data_dir


def test_stitching(
    params: Params,
    data_dir: Path,
    tmp_path: Path,
):
    stitcher = Stitcher()

    target_path = tmp_path / uuid4().hex

    stitcher.run_stitch(
        src_dir=data_dir,
        target=target_path,
        params=params,
    )

    assert target_path.exists()
    assert (data_dir / params.output_file_name).exists()
