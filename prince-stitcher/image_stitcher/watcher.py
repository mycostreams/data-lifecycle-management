import asyncio
import os
from pathlib import Path

from watchfiles import Change, awatch

from .consumer import Consumer, Handler
from .log import configure_logging


def last_image_frame(change: Change, path: str):
    return change == Change.added and Path(path).name == "Img_r10_c15.tif"


async def main():

    configure_logging()

    data_dir = os.getenv("DATA_DIR")

    queue = asyncio.Queue[Path]()

    async with Handler() as handler:
        async with Consumer(handler=handler, queue=queue):
            async for changes in awatch(data_dir, watch_filter=last_image_frame):
                for _, path in changes:
                    queue.put_nowait(Path(path).parent)


if __name__ == "__main__":
    asyncio.run(main())
