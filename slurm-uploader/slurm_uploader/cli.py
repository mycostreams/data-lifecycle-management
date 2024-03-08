import asyncio
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

from .client import Client
from .config import Settings, get_connection_url
from .publisher import publisher
from .subscriber import subscriber

ConnectionUrlT = Annotated[Optional[str], typer.Option()]

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
    connection_url: ConnectionUrlT = None,
):
    """
    Publish a JOB_ID via the message broker.
    """
    connection_url = get_connection_url(connection_url)

    asyncio.run(publisher(connection_url, job_id))


@app.command()
def subscribe(
    connection_url: ConnectionUrlT = None,
):
    """
    Subscribe to messages
    """
    connection_url = get_connection_url(connection_url)

    asyncio.run(subscriber(connection_url))


if __name__ == "__main__":
    typer.run(app)
