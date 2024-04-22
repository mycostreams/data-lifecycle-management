from functools import lru_cache
from pathlib import Path

import httpx

from .dto import DirectoryConfig, TimestepMeta

DOWNLOAD_URL = "https://vu.data.surfsara.nl/index.php/s/ndI1UoMRwliVYGR/download"


@lru_cache
def _get_image(url: str = DOWNLOAD_URL):
    response = httpx.get(url)
    return response.content


def make_timestep_directory(
    target_dir: Path,
    meta: TimestepMeta,
    config: DirectoryConfig | None = None,
) -> None:
    """Construct a new timestep directory."""
    config = config or DirectoryConfig()

    img_dir = target_dir / config.img_dir_name
    img_dir.mkdir(parents=True, exist_ok=True)

    img = img_dir / "Img_r10_c15.tif"
    img.write_bytes(_get_image())

    param_file = target_dir / config.param_filename
    param_file.write_text(meta.model_dump_json(indent=4, by_alias=True))