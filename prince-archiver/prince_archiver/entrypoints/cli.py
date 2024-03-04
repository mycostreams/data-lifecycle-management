from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

from prince_archiver.dto import ExperimentDTO
from prince_archiver.utils import make_timestep_directory as _make_timestep_directory

app = typer.Typer()


@app.command()
def make_timestep_directory(
    data_dir: Path,
    timestamp: Annotated[Optional[datetime], typer.Argument()] = None,
):
    experiment = ExperimentDTO(plate=1, CrossDate=date(2000, 1, 1))

    _make_timestep_directory(
        experiment=experiment,
        timestamp=timestamp or datetime.now(),
        target_dir=data_dir,
    )


if __name__ == "__main__":
    typer.run(make_timestep_directory)
