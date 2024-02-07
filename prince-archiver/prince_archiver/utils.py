from datetime import datetime
from pathlib import Path
from typing import Generator

from .dto import ExperimentMeta, PlateTimestep

PARAM_FILE = "param.json"
IMAGE_FOLDER = "Img"


def parse_folder_name(filename: str) -> tuple[int, datetime]:

    time, plate = filename.split("_Plate")

    return int(plate), datetime.strptime(time, "%Y%m%d_%H%M")


def get_plate_timesteps(
    data_dir: Path,
    *,
    param_file: str = PARAM_FILE,
    image_folder: str = IMAGE_FOLDER,
) -> Generator[PlateTimestep, None, None]:
    """Iterate over plate timesteps."""
    for folder in data_dir.iterdir():

        # Extract info from folder name
        plate, timestamp = parse_folder_name(folder.name)

        # Extract info from file
        param_file_path = folder / param_file
        experiment_meta = ExperimentMeta.model_validate_json(
            param_file_path.read_bytes(),
        )

        # Collect file info
        image_folder_path = folder / image_folder
        image_count = len(list(image_folder_path.iterdir()))

        yield PlateTimestep(
            experiment_id=experiment_meta.id,
            prince_position=plate,
            timestamp=timestamp,
            raw_img_path=image_folder_path,
            img_count=image_count,
        )
