from functools import lru_cache, partial
from pathlib import Path
from typing import Generator

import httpx

from .dto import DirectoryConfig, TimestepDTO, TimestepMeta

DOWNLOAD_URL = "https://vu.data.surfsara.nl/index.php/s/ndI1UoMRwliVYGR/download"


def parse_timestep_dir(
    path: Path,
    *,
    config: DirectoryConfig | None = None,
) -> TimestepDTO:
    config = config or DirectoryConfig()

    param_path = path / config.param_filename

    timestep_meta = TimestepMeta.model_validate_json(param_path.read_bytes())

    return TimestepDTO(
        timestep_dir_name=path.name,
        img_dir_name=config.img_dir_name,
        **timestep_meta.model_dump(),
    )


def get_plate_timesteps(
    data_dir: Path,
    *,
    config: DirectoryConfig | None = None,
) -> Generator[TimestepDTO, None, None]:
    """Iterate over plate timesteps."""
    func = partial(
        parse_timestep_dir,
        config=config or DirectoryConfig(),
    )

    for item in map(func, data_dir.iterdir()):
        yield item


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
