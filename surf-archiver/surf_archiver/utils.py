import asyncio
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import date
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import AsyncGenerator

from s3fs import S3FileSystem


def tar(source: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with TarFile.open(dest, "w") as tar:
        tar.add(source, arcname=".")


async def atar(source: Path, dest: Path, pool: ProcessPoolExecutor):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(pool, tar, source, dest)


@asynccontextmanager
async def managed_file_system() -> AsyncGenerator[S3FileSystem, None]:

    s3 = S3FileSystem(asynchronous=True)

    session = await s3.set_session()

    yield s3

    await session.close()


async def run_archiving(
    date: date,
    bucket_name: str,
    target_dir: Path,
):
    date_str = date.strftime("%Y%m%d")

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
