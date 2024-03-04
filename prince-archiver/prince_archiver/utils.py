from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Generator

from .dto import BaseTimestepDTO, ExperimentDTO


@dataclass(kw_only=True)
class TimestepConfig:

    param_filename = "param.json"
    img_dir_name: str = "Img"
    final_img_name: str = "Img_r10_c15.tif"


def parse_folder_name(filename: str) -> tuple[int, datetime]:

    time, plate = filename.split("_Plate")

    return int(plate), datetime.strptime(time, "%Y%m%d_%H%M")


def parse_timestep_dir(
    path: Path,
    *,
    config: TimestepConfig | None = None,
) -> BaseTimestepDTO:

    config = config or TimestepConfig()

    position, timestamp = parse_folder_name(path.name)

    param_path = path / config.param_filename
    img_dir = path / config.img_dir_name

    experiment = ExperimentDTO.model_validate_json(param_path.read_bytes())
    image_count = len(list(img_dir.iterdir()))

    return BaseTimestepDTO(
        experiment=experiment,
        prince_position=position,
        timestamp=timestamp,
        raw_img_path=path / config.img_dir_name,
        img_count=image_count,
    )


def get_plate_timesteps(
    data_dir: Path, *, config: TimestepConfig | None = None
) -> Generator[BaseTimestepDTO, None, None]:
    """Iterate over plate timesteps."""
    func = partial(
        parse_timestep_dir,
        config=config or TimestepConfig(),
    )

    for item in map(func, data_dir.iterdir()):
        yield item


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
    img.touch()

    return dir_path
