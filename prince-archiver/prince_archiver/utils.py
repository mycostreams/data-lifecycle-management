from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache, partial
from pathlib import Path
from typing import Generator
from uuid import uuid4

import httpx

from .dto import ExperimentDTO, TimestepDTO

DOWNLOAD_URL = "https://vu.data.surfsara.nl/index.php/s/ndI1UoMRwliVYGR/download"


@dataclass(kw_only=True)
class TimestepConfig:

    param_filename = "param.json"
    img_dir_name: str = "Img"
    final_img_name: str = "Img_r10_c15.tif"


def get_random_id() -> str:
    return uuid4().hex[:6]


def parse_folder_name(filename: str) -> tuple[int, datetime]:

    time, plate = filename.split("_Plate")

    return int(plate), datetime.strptime(time, "%Y%m%d_%H%M")


def parse_timestep_dir(
    path: Path,
    *,
    config: TimestepConfig | None = None,
) -> TimestepDTO:

    config = config or TimestepConfig()

    position, timestamp = parse_folder_name(path.name)

    param_path = path / config.param_filename

    experiment = ExperimentDTO.model_validate_json(param_path.read_bytes())

    return TimestepDTO(
        experiment=experiment,
        prince_position=position,
        timestamp=timestamp,
        base_path=path.parent.resolve(),
        timestep_dir_name=path.name,
        img_dir_name=config.img_dir_name,
    )


def get_plate_timesteps(
    data_dir: Path,
    *,
    config: TimestepConfig | None = None,
) -> Generator[TimestepDTO, None, None]:
    """Iterate over plate timesteps."""
    func = partial(
        parse_timestep_dir,
        config=config or TimestepConfig(),
    )

    for item in map(func, data_dir.iterdir()):
        yield item


@lru_cache
def _get_image(url: str = DOWNLOAD_URL):
    response = httpx.get(url)
    return response.content


def make_timestep_directory(
    *,
    experiment: ExperimentDTO,
    prince_position: int = 1,
    timestamp: datetime,
    target_dir: Path,
    config: TimestepConfig | None = None,
) -> Path:
    """Construct a new timestep directory."""
    timestamp_string = timestamp.strftime("%Y%m%d_%H%M")

    config = config or TimestepConfig()

    dir_name = f"{timestamp_string}_Plate{prince_position:02}"
    dir_path = target_dir / dir_name

    img_dir = dir_path / config.img_dir_name
    img_dir.mkdir(parents=True, exist_ok=True)

    param_file = dir_path / config.param_filename
    param_file.write_text(experiment.model_dump_json(indent=4, by_alias=True))

    img = img_dir / config.final_img_name
    img.write_bytes(_get_image())

    return dir_path
