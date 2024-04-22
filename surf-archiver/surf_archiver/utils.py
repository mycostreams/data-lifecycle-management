import asyncio
from collections import defaultdict
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import AsyncGenerator, Union

from s3fs import S3FileSystem


def tar(src: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    with TarFile.open(target, "w") as tar:
        tar.add(src, arcname=".")


async def atar(src: Path, target: Path, executor: Executor):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, tar, src, target)


@asynccontextmanager
async def managed_file_system() -> AsyncGenerator[S3FileSystem, None]:
    s3 = S3FileSystem(asynchronous=True)

    session = await s3.set_session()

    yield s3

    await session.close()


async def run_archiving(
    date_: Union[date, datetime],
    bucket_name: str,
    target_dir: Path,
):
    date_str = date_.strftime("%Y%m%d")

    async with AsyncExitStack() as stack:
        temp_dir = Path(stack.enter_context(TemporaryDirectory()))
        pool = stack.enter_context(ProcessPoolExecutor())
        s3 = await stack.enter_async_context(managed_file_system())

        files = map(Path, await s3._glob(f"{bucket_name}/*/{date_str}*.tar"))
        data: dict[str, list[Path]] = defaultdict(list)
        for file in files:
            data[file.parent.name].append(file)

        tar_futures = []
        for experiment_id, files in data.items():
            experiment_temp_dir = temp_dir / experiment_id
            await s3._get(files, f"{experiment_temp_dir}/", batch_size=-1)

            experiment_target_dir = target_dir / experiment_id / f"{date_str}.tar"
            tar_futures.append(
                asyncio.create_task(
                    atar(experiment_temp_dir, experiment_target_dir, pool),
                )
            )

        await asyncio.gather(*tar_futures)
