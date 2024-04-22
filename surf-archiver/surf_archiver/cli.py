import asyncio
from datetime import datetime
from pathlib import Path

import typer

from .utils import run_archiving

app = typer.Typer()

DEFAULT_BUCKET_NAME = "prince-data-dev"
DEFAULT_DIR = Path.home() / "prince"


@app.command()
def now():
    typer.echo(datetime.now().isoformat())


@app.command()
def archive(
    date: datetime,
    bucket_name: str = DEFAULT_BUCKET_NAME,
    target_dir: Path = DEFAULT_DIR,
):
    asyncio.run(run_archiving(date, bucket_name, target_dir))
