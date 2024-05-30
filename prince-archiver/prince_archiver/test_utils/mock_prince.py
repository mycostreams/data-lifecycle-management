import asyncio
import logging
import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI

from prince_archiver.dto import TimestepMeta
from prince_archiver.logging import configure_logging
from prince_archiver.utils import now

from .utils import make_timestep_directory

BASE_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))

LOGGER = logging.getLogger(__name__)


def _create_meta() -> TimestepMeta:
    return TimestepMeta(
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=now(),
    )


def create_app() -> FastAPI:

    app = FastAPI()

    @app.post("/timestep")
    def create_timestep(data: TimestepMeta):
        target_dir = BASE_DIR / uuid4().hex[:4]
        LOGGER.info("Added directory")
        make_timestep_directory(target_dir=target_dir, meta=data)

    return app


async def main():
    """Add new timestep directory every minute."""
    configure_logging()

    transport = httpx.ASGITransport(app=create_app())

    client = httpx.AsyncClient(transport=transport, base_url="http://mockprince")
    async with client:
        while True:
            meta = _create_meta()
            await client.post("/timestep", data=meta.model_dump(mode="json"))
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
