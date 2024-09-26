from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer

from prince_archiver.definitions import System
from prince_archiver.service_layer.external_dto import TimestepMeta
from prince_archiver.test_utils.utils import make_timestep_directory
from prince_archiver.utils import now

app = typer.Typer()

DataDirT = Annotated[Path, typer.Option(envvar="DATA_DIR")]


@app.command()
def populate_data_dir(data_dir: DataDirT):
    for system in System:
        events_dir = data_dir / system / "events"
        events_dir.mkdir(parents=True, exist_ok=True)


@app.command()
def make_timestep_dir(
    data_dir: DataDirT,
    timestamp: Annotated[datetime, typer.Option(default_factory=now)],
):
    meta = TimestepMeta(
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=timestamp,
        path=Path(uuid4().hex[:6]),
    )

    make_timestep_directory(meta, data_dir)
