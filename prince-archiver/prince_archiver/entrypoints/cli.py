from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

from prince_archiver.dto import TimestepMeta
from prince_archiver.test_utils import (
    make_timestep_directory as _make_timestep_directory,
)

app = typer.Typer()


@app.command()
def make_timestep_directory(
    data_dir: Path,
    timestamp: Annotated[Optional[datetime], typer.Argument()] = None,
):
    meta = TimestepMeta(
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=timestamp or datetime.now(),
    )

    _make_timestep_directory(data_dir, meta)


if __name__ == "__main__":
    typer.run(make_timestep_directory)
