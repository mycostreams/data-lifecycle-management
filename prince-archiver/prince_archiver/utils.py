from datetime import UTC, datetime
from pathlib import Path
from typing import Generator

from .dto import TimestepDTO


def now() -> datetime:
    return datetime.now(UTC)


def parse_timestep_dir(path: Path) -> TimestepDTO:
    return TimestepDTO.model_validate_json(path.read_bytes())


def get_plate_timesteps(data_dir: Path) -> Generator[TimestepDTO, None, None]:
    """Iterate over plate timesteps."""
    yield from map(parse_timestep_dir, data_dir.iterdir())
