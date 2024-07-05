import asyncio
import logging
import os
from concurrent.futures import Executor
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path

from aiofiles.tempfile import NamedTemporaryFile, TemporaryDirectory
from pydantic import BaseModel
from s3fs import S3FileSystem

from .stitcher import AbstractStitcher, Params, Stitcher
from .utils import Dimensions, resize_image

LOGGER = logging.getLogger(__name__)


BASE_PATH = ContextVar("BASE_PATH", default=os.getenv("DATA_DIR", ""))


class Message(BaseModel):
    experiment_id: str
    local_path: Path
    timestamp: datetime
    dimensions: Dimensions = Dimensions(1024, 750)
    grid_size: Dimensions = Dimensions(15, 10)


class Handler:
    """Handler used for processing new directories."""

    def __init__(
        self,
        s3: S3FileSystem | None = None,
        stitcher: AbstractStitcher | None = None,
    ):
        self.stitcher = stitcher or Stitcher()
        self.s3 = s3 or S3FileSystem(..., asynchronous=True)
        self.pool: Executor | None = None

    async def __call__(self, message: Message):
        LOGGER.info(f"Received {message.local_path.name} for processing")

        target_key = "{experiment_id}/{date_str}.tif".format(
            experiment_id=message.experiment_id,
            date_str=message.timestamp.strftime("%Y%m%d_%H%M"),
        )

        async with (
            TemporaryDirectory() as _temp_dir,
            NamedTemporaryFile() as _temp_file,
        ):
            temp_dir = Path(_temp_dir)
            temp_file = Path(_temp_file.name)

            await self.resize_directory(
                src=Path(BASE_PATH.get()) / message.local_path,
                target=temp_dir,
                dimensions=message.dimensions,
            )

            await self.run_stitch(
                src=temp_dir, target=temp_file, grid_size=message.grid_size
            )

            await self.upload(src=temp_file, target=target_key)

    async def resize_directory(
        self,
        src: Path,
        target: Path,
        dimensions: Dimensions,
    ):
        LOGGER.info("Resizing directory")

        loop = asyncio.get_event_loop()

        resize_args = (
            (file, target / file.name, dimensions) for file in src.glob("*.tif")
        )
        resize_jobs = (
            loop.run_in_executor(self.pool, resize_image, *args) for args in resize_args
        )
        await asyncio.gather(*resize_jobs)

        LOGGER.info("Resized directory")

    async def run_stitch(self, src: Path, target: Path, grid_size: Dimensions):
        LOGGER.info("Starting stitching")

        params = Params(grid_size_x=grid_size.x, grid_size_y=grid_size.y)
        await asyncio.to_thread(self.stitcher.run_stitch, src, target, params)

        LOGGER.info("Completed stitching")

    async def upload(self, src: Path, target: str):
        LOGGER.info("Uploading to S3")

        await self.s3._put(src.as_posix(), f"fast-stitcher-dev/{target}")

        LOGGER.info("Uploaded to S3")

    async def __aenter__(self) -> "Handler":
        self.stack = await AsyncExitStack().__aenter__()

        self.pool = self.stack.enter_context(ProcessPoolExecutor())
        await self.stack.enter_async_context(self.s3_session_manager())

        return self

    async def __aexit__(self, *args, **kwargs):
        await self.stack.__aexit__(*args, **kwargs)

    @asynccontextmanager
    async def s3_session_manager(self):
        session = await self.s3.set_session()

        yield session

        await session.close()
