import asyncio
import logging
from datetime import date
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, Response
from pydantic_settings import BaseSettings

from prince_archiver.log import configure_logging
from prince_archiver.service_layer.external_dto import TimestepMeta
from prince_archiver.test_utils.utils import make_timestep_directory
from prince_archiver.utils import now

LOGGER = logging.getLogger(__name__)


class Settings(BaseSettings):
    INTERVAL: int = 30
    DATA_DIR: Path


def _create_meta() -> TimestepMeta:
    return TimestepMeta(
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=now(),
        path=Path(uuid4().hex[:6]),
    )


def create_app(*, settings: Settings | None = None) -> FastAPI:
    app = FastAPI()

    settings = settings or Settings()

    @app.post("/timestep", status_code=200)
    def create_timestep(data: TimestepMeta) -> Response:
        logging.info("[%s] Added timestep", data.timestep_id)
        make_timestep_directory(meta=data, base_dir=settings.DATA_DIR)
        return Response(status_code=200)

    return app


async def main():
    """Add new timestep directory every minute."""
    configure_logging()

    logging.info("Starting up mock prince")

    settings = Settings()

    transport = httpx.ASGITransport(app=create_app(settings=settings))

    client = httpx.AsyncClient(transport=transport, base_url="http://mockprince")
    async with client:
        while True:
            meta = _create_meta()
            await client.post(
                "/timestep",
                json=meta.model_dump(mode="json", by_alias=True),
            )
            await asyncio.sleep(settings.INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
