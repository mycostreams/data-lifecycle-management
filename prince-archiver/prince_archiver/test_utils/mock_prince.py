import asyncio
import logging
import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, Response

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
        img_dir=uuid4().hex[:6],
    )


def create_app() -> FastAPI:

    app = FastAPI()

    @app.post("/timestep", status_code=200)
    def create_timestep(data: TimestepMeta) -> Response:
        logging.info("Added timestep")
        make_timestep_directory(meta=data, base_dir=BASE_DIR)
        return Response(status_code=200)

    return app


async def main():
    """Add new timestep directory every minute."""
    configure_logging()

    logging.info("Starting up mock prince")

    transport = httpx.ASGITransport(app=create_app())

    client = httpx.AsyncClient(transport=transport, base_url="http://mockprince")
    async with client:
        while True:
            meta = _create_meta()
            await client.post(
                "/timestep",
                json=meta.model_dump(mode="json"),
            )
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
