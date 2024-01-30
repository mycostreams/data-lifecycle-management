from datetime import datetime
from hashlib import file_digest
from pathlib import Path
from shutil import make_archive
from typing import Callable, Generator
from uuid import uuid4

from .dto import Archive, ArchivedPlateTimestep, ExperimentMeta, PlateTimestep

PARAM_FILE = "param.json"
IMAGE_FOLDER = "Img"


def make_hashed_archive(source: Path, target: Path):

    make_archive(
        base_name=str(target.parent / target.stem),
        format=target.suffix.strip("."),
        root_dir=source.parent,
        base_dir=source.name,
    )

    with target.open("rb") as file:
        archive_hash = file_digest(file, "sha256").hexdigest()

    return Archive(
        path=target,
        hash=archive_hash,
    )


def archive_plate_timestep(
    plate_timestep: PlateTimestep,
    *,
    target_dir: Path,
    _filename: str | None = None,
    _archiver_func: Callable[[Path, Path], Archive] = make_hashed_archive,
) -> ArchivedPlateTimestep:

    filename = _filename or f"{uuid4().hex[:6]}.zip"

    archive_path = target_dir / filename
    archive = _archiver_func(plate_timestep.raw_img_path, archive_path)

    return ArchivedPlateTimestep(
        plate_timestep=plate_timestep,
        archive=archive,
    )


def parse_folder_name(filename: str) -> tuple[int, datetime]:

    time, plate = filename.split("_Plate")

    return int(plate), datetime.strptime(time, "%Y%m%d_%H%M")


def get_plate_timesteps(
    data_dir: Path,
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
