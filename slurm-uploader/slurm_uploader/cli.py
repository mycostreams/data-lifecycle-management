import asyncio
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

from .client import Client
from .config import DEFAULT_CONNECTION_URL, Settings
from .publisher import publisher
from .subscriber import subscriber

ConnectionUrlT = Annotated[Optional[str], typer.Argument(envvar="CONNECTION_URL")]


app = typer.Typer()


@app.command()
def submit(
    timestamp: datetime,
    env_file: Annotated[Path, typer.Argument()] = Path(".env"),
):
    """
    Submit a day for processing.
    """
    settings = Settings(_env_file=env_file)
    client = Client(**{k.lower(): v for k, v in settings.model_dump().items()})
    with client:
        print(client.submit_job(timestamp))


@app.command()
def publish(
    job_id: str,
    connection_url: ConnectionUrlT = DEFAULT_CONNECTION_URL,
):
    """
    Publish a JOB_ID via the message broker.
    """
    asyncio.run(publisher(connection_url, job_id))


@app.command()
def subscribe(
    connection_url: ConnectionUrlT = DEFAULT_CONNECTION_URL,
):
    """
    Subscribe to messages
    """
    asyncio.run(subscriber(connection_url))


if __name__ == "__main__":
    typer.run(app)
