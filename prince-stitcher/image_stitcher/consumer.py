import asyncio
import logging
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from pathlib import Path
from typing import Awaitable, Callable

from aiofiles.tempfile import NamedTemporaryFile, TemporaryDirectory
from s3fs import S3FileSystem

from .stitcher import AbstractStitcher, Stitcher
from .utils import resize_image

LOGGER = logging.getLogger(__name__)


class Handler:
    """Handler used for processing new directories."""

    def __init__(
        self,
        s3: S3FileSystem | None = None,
        stitcher: AbstractStitcher | None = None,
    ):
        self.stitcher = stitcher or Stitcher()
        self.s3 = s3 or S3FileSystem(..., asynchronous=True)

    async def __call__(self, path: Path):
        LOGGER.info(f"Received {path.name} for processing")

        async with (
            TemporaryDirectory() as _temp_dir,
            NamedTemporaryFile() as _temp_file,
        ):
            temp_dir = Path(_temp_dir)
            temp_file = Path(_temp_file.name)

            await self.resize_directory(src=path, target=temp_dir)
            await self.run_stitch(src=temp_dir, target=temp_file)
            await self.upload(src=temp_file, target=f"{path.name}.tif")

    async def resize_directory(self, src: Path, target: Path):
        LOGGER.info("Resizing directory")

        loop = asyncio.get_event_loop()

        resize_jobs = map(
            lambda args: loop.run_in_executor(self.pool, resize_image, *args),
            map(lambda file: (file, target / file.name), src.glob("*.tif")),
        )
        await asyncio.gather(*resize_jobs)

        LOGGER.info("Resized directory")

    async def run_stitch(self, src: Path, target: Path):
        LOGGER.info("Starting stitching")

        await asyncio.to_thread(self.stitcher.run_stitch, src, target)

        LOGGER.info("Completed stitching")

    async def upload(self, src: Path, target: str):
        LOGGER.info("Uploading to S3")

        await self.s3._put(src.as_posix(), f"fast-stitcher-dev/{target}")

        LOGGER.info("Uploaded to S3")

    async def __aenter__(self) -> "Consumer":
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


class Consumer:
    """Consumer used to deletegate processing."""

    def __init__(
        self,
        *,
        handler: Callable[[Path], Awaitable[None]],
        queue: asyncio.Queue[Path] | None = None,
    ):
        self.handler = handler
        self.queue = queue or asyncio.Queue[Path]()

    async def worker(self):
        while True:

            timestep = await self.queue.get()

            await self.handler(timestep)

            self.queue.task_done()

    async def __aenter__(self) -> "Consumer":
        self.stack = await AsyncExitStack().__aenter__()

        # Now start the actual worker
        self.stack.enter_context(self.worker_manager())

        LOGGER.info("Consumer running")

        return self

    async def __aexit__(self, *args, **kwargs):
        await self.stack.__aexit__(*args, **kwargs)

    @contextmanager
    def worker_manager(self):
        LOGGER.info("Worker starting up")

        worker_task = asyncio.create_task(self.worker())

        yield worker_task

        LOGGER.info("Worker shutting down")

        self.queue.join()
        worker_task.cancel()
