from functools import lru_cache
from pathlib import Path
from shutil import copy
from timeit import default_timer

import httpx

DOWNLOAD_URL = "https://vu.data.surfsara.nl/index.php/s/ndI1UoMRwliVYGR/download"


class Timer:
    def __init__(self):
        self.ref = default_timer()

    @property
    def delta(self) -> float:
        return default_timer() - self.ref


@lru_cache
def _get_image(url: str = DOWNLOAD_URL):
    response = httpx.get(url)
    return response.content


def make_timestep_directory(
    target_dir: Path,
    src_img: Path | None = None,
) -> None:
    """Construct a new timestep directory."""
    target_dir.mkdir(parents=True, exist_ok=True)

    img = target_dir / "Img_r10_c15.tif"
    if src_img:
        copy(src_img, img)
    else:
        img.write_bytes(_get_image())
