from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Generator

from .dto import BaseTimestepDTO, ExperimentDTO

PARAM_FILE = "param.json"
IMAGE_FOLDER = "Img"


def parse_folder_name(filename: str) -> tuple[int, datetime]:

    time, plate = filename.split("_Plate")

    return int(plate), datetime.strptime(time, "%Y%m%d_%H%M")


def parse_timestep_dir(
    path: Path,
    *,
    param_file: str = PARAM_FILE,
    image_folder: str = IMAGE_FOLDER,
) -> BaseTimestepDTO:

    param_path = path / param_file
    img_path = path / image_folder

    position, timestamp = parse_folder_name(path.name)

    experiment = ExperimentDTO.model_validate_json(param_path.read_bytes())
    image_count = len(list(path.iterdir()))

    return BaseTimestepDTO(
        experiment=experiment,
        prince_position=position,
        timestamp=timestamp,
        raw_img_path=img_path,
        img_count=image_count,
    )


def get_plate_timesteps(
    data_dir: Path,
    *,
    param_file: str = PARAM_FILE,
    image_folder: str = IMAGE_FOLDER,
) -> Generator[BaseTimestepDTO, None, None]:
    """Iterate over plate timesteps."""

    func = partial(
        parse_timestep_dir,
        param_file=param_file,
        image_folder=image_folder,
    )

    for item in map(func, data_dir.iterdir()):
        yield item
