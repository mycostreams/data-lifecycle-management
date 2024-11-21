import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Response
from pydantic import FilePath, RedisDsn
from pydantic_settings import BaseSettings

from prince_archiver.adapters.streams import Stream
from prince_archiver.log import configure_logging
from prince_archiver.service_layer.dto import NewImagingEvent
from prince_archiver.service_layer.streams import Message, Streams
from prince_archiver.test_utils.utils import make_timestep_directory
from prince_archiver.utils import now

LOGGER = logging.getLogger(__name__)


class Settings(BaseSettings):
    INTERVAL: int = 30
    DATA_DIR: Path
    REDIS_DSN: RedisDsn
    SRC_IMG: FilePath


def _create_event() -> NewImagingEvent:
    ref_id = uuid4()
    return NewImagingEvent(
        ref_id=ref_id,
        experiment_id="test-id",
        timestamp=now(),
        type="stitch",
        system="prince",
        img_count=1,
        metadata={
            "application": {
                "application": "mock-prince",
                "version": "v0.1.0",
                "user": "mock-user",
            },
            "camera": {
                "model": "mock-model",
                "station_name": "mock-station",
                "exposure_time": 0.01,
                "frame_rate": None,
                "frame_size": (1, 1),
                "binning": "1x1",
                "gain": 1,
                "gamma": 1,
                "intensity": [0, 0, 0],
                "bits_per_pixel": 0,
            },
            "stitching": {
                "last_focused_at": "2000-01-01T00:00:00+00:00",
                "grid_size": (1, 1),
            },
        },
        local_path=ref_id.hex[:6],
    )


def create_app(*, settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    client = redis.from_url(str(settings.REDIS_DSN))

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with client:
            yield

    stream = Stream(name=Streams.imaging_events, redis=client)

    app = FastAPI(lifespan=lifespan)

    @app.post("/timestep", status_code=200)
    async def create_event(data: NewImagingEvent) -> Response:
        logging.info("[%s] Added timestep", data.ref_id)

        make_timestep_directory(
            target_dir=settings.DATA_DIR / data.system / data.local_path,
            src_img=settings.SRC_IMG,
        )

        await stream.add(Message(data))

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
            meta = _create_event()
            async with asyncio.TaskGroup() as tg:
                tg.create_task(asyncio.sleep(settings.INTERVAL))

                tg.create_task(
                    client.post(
                        "/timestep",
                        json=meta.model_dump(mode="json", by_alias=True),
                    )
                )


if __name__ == "__main__":
    asyncio.run(main())
