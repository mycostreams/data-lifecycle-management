import asyncio
import tarfile
from concurrent import futures
from contextlib import AsyncExitStack, asynccontextmanager
from functools import partial
from pathlib import Path
from typing import AsyncGenerator

import aiofiles
import aiofiles.os
import cv2
import s3fs
from pydantic import validate_call

from .config import Settings, get_settings
from .dto import TimestepDTO


def compress(src: Path, target: Path):
    img = cv2.imread(str(src))
    cv2.imwrite(
        str(target),
        img,
        params=(cv2.IMWRITE_TIFF_COMPRESSION, 5),
    )


def tar(src: Path, target: Path):
    with tarfile.open(src, "w") as tar:
        tar.add(target, arcname=".")


@validate_call
async def workflow(ctx: dict, data: TimestepDTO):

    loop = asyncio.get_event_loop()

    acompress = partial(loop.run_in_executor, ctx["pool"], compress)
    atar = partial(loop.run_in_executor, ctx["pool"], zip)

    settings: Settings = ctx["settings"]
    s3: s3fs.S3FileSystem = ctx["s3"]

    archive_path = settings.ARCHIVE_DIR / data.key
    img_dir = settings.DATA_DIR / data.timestep_dir_name / data.img_dir_name

    files = filter(
        lambda f: f.suffix == ".tif",
        map(Path, await aiofiles.os.listdir(img_dir)),
    )

    async with aiofiles.tempfile.TemporaryDirectory() as _temp_dir:
        temp_dir = Path(_temp_dir)

        futures = (acompress(file, temp_dir / file.name) for file in files)

        await asyncio.gather(*futures)
        await atar(temp_dir, archive_path)

    await s3._put_file(archive_path, f"{settings.AWS_BUCKET_NAME}/{data.key}")


@asynccontextmanager
async def managed_file_system(
    settings: Settings,
) -> AsyncGenerator[s3fs.S3FileSystem, None]:
    s3 = s3fs.S3FileSystem(
        key=settings.AWS_ACCESS_KEY_ID,
        secret=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        asynchronous=True,
    )

    session = await s3.set_session()

    yield s3

    await session.close()


async def startup(ctx):
    settings = get_settings()
    ctx["settings"] = settings

    exit_stack = await AsyncExitStack().__aenter__()
    ctx["exit_stack"] = exit_stack

    ctx["pool"] = exit_stack.enter_context(futures.ProcessPoolExecutor())
    ctx["s3"] = await exit_stack.enter_async_context(managed_file_system(settings))


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:

    functions = [workflow]
    on_startup = startup
    on_shutdown = shutdown
