import asyncio
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack
from pathlib import Path

import aiofiles
import aiofiles.os
import s3fs
from aiofiles.tempfile import TemporaryDirectory
from arq.connections import RedisSettings

from .config import WorkerSettings as _WorkerSettings
from .config import get_worker_settings
from .dto import TimestepDTO
from .file import acompress, atar, managed_file_system
from .logging import configure_logging

LOGGER = logging.getLogger(__name__)


async def workflow(ctx: dict, input_data: dict):

    data = TimestepDTO.model_validate(input_data)

    settings: _WorkerSettings = ctx["settings"]
    s3: s3fs.S3FileSystem = ctx["s3"]
    pool: ProcessPoolExecutor = ctx["pool"]

    img_dir = settings.DATA_DIR / data.timestep_dir_name / data.img_dir_name
    files = map(lambda path: img_dir / path, await aiofiles.os.listdir(img_dir))

    async with AsyncExitStack() as stack:
        temp_dirs = await asyncio.gather(
            *(stack.enter_async_context(TemporaryDirectory()) for _ in range(2)),
        )
        temp_img_dir, temp_archive_dir = map(Path, temp_dirs)
        temp_archive_path = temp_archive_dir / data.archive_name

        await asyncio.gather(
            *(acompress(file, temp_img_dir / file.name, pool) for file in files),
        )
        await atar(temp_img_dir, temp_archive_path, pool)

        await s3._put_file(temp_archive_path, f"{settings.AWS_BUCKET_NAME}/{data.key}")


async def startup(ctx):
    configure_logging()

    settings = get_worker_settings()
    ctx["settings"] = settings

    exit_stack = await AsyncExitStack().__aenter__()
    ctx["exit_stack"] = exit_stack

    ctx["pool"] = exit_stack.enter_context(ProcessPoolExecutor())
    ctx["s3"] = await exit_stack.enter_async_context(managed_file_system(settings))


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:

    functions = [workflow]
    on_startup = startup
    on_shutdown = shutdown

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
