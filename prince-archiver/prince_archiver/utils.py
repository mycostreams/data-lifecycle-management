from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Generator

from .dto import DirectoryConfig, TimestepDTO, TimestepMeta


def now() -> datetime:
    return datetime.now(UTC)


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
