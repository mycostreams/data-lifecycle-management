from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Optional
from uuid import uuid4

import typer

from prince_archiver.dto import TimestepMeta

from .utils import make_timestep_directory as _make_timestep_directory

app = typer.Typer()

DataDirT = Annotated[Path, typer.Argument(envvar="DATA_DIR")]


@app.command()
def init(data_dir: DataDirT):
    events_dir = data_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)


@app.command()
def make_timestep_directory(
    data_dir: DataDirT,
    timestamp: Annotated[Optional[datetime], typer.Argument()] = None,
):
    meta = TimestepMeta(
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=timestamp or datetime.now(),
        path=Path(uuid4().hex[:6]),
    )

    _make_timestep_directory(meta, data_dir)


if __name__ == "__main__":
    typer.run(make_timestep_directory)
