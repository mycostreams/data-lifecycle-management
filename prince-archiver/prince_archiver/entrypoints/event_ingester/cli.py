import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

import redis.asyncio as redis
import typer

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.streams import Streams

from .functions import State
from .ingester import managed_event_ingester
from .settings import Settings

app = typer.Typer()


@asynccontextmanager
async def managed_state(
    redis_dsn: str,
    src_dir: Path,
    copy_to_staging: bool,
) -> AsyncGenerator[State, None]:
    redis_client = redis.from_url(redis_dsn)
    async with redis_client:
        yield State(
            settings=Settings(
                SRC_DIR=src_dir,
                COPY_TO_STAGING=copy_to_staging,
            ),
            stream=Stream(
                redis=redis_client,
                stream=Streams.new_imaging_event,
            ),
            path_manager=PathManager(src_dir),
        )


async def aingest_backlog(
    start: datetime,
    end: datetime,
    redis_dsn: str,
    src_dir: Path,
    copy_to_staging: bool,
):
    async with (
        managed_state(redis_dsn, src_dir, copy_to_staging) as state,
        managed_event_ingester(state) as event_ingester,
    ):
        await event_ingester.ingest_backlog(start=start, end=end)


@app.command()
def ingest_backlog(
    start: datetime,
    end: datetime,
    redis_dsn: Annotated[str, typer.Option(envvar="REDIS_DSN")],
    src_dir: Annotated[Path, typer.Option(envvar="SRC_DIR")],
    copy_to_staging: Annotated[bool, typer.Option(envvar="COPY_TO_STAGING")] = False,
):
    asyncio.run(
        aingest_backlog(
            start=start.astimezone(),
            end=end.astimezone(),
            redis_dsn=redis_dsn,
            src_dir=src_dir,
            copy_to_staging=copy_to_staging,
        )
    )
