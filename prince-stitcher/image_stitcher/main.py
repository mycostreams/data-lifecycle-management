from multiprocessing import Pool
from pathlib import Path
from tempfile import TemporaryDirectory

from .stitcher import AbstractStitcher, Stitcher
from .utils import resize_image


def stitch_timestep(
    dir: Path,
    target: Path = Path("./stitched.tif"),
    *,
    stitcher: AbstractStitcher | None = None,
):
    stitcher = stitcher or Stitcher()

    with TemporaryDirectory() as _temp_dir:
        temp_dir = Path(_temp_dir)

        # Resize images
        star_args = ((file, temp_dir / file.name) for file in dir.glob("*.tif"))
        with Pool() as pool:
            pool.starmap(resize_image, star_args)

        # stitch image
        stitcher.run_stitch(temp_dir, target)
