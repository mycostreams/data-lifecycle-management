import asyncio
import os
from datetime import datetime
from pathlib import Path

from watchfiles import Change, awatch

from .consumer import Consumer, Handler, Message
from .log import configure_logging


def last_image_frame(change: Change, path: str):
    return change == Change.added and Path(path).name == "Img_r10_c15.tif"


async def main():
    configure_logging()

    data_dir = os.getenv("DATA_DIR")

    queue = asyncio.Queue[Message]()

    async with Handler() as handler:
        async with Consumer(handler=handler, queue=queue):
            async for changes in awatch(data_dir, watch_filter=last_image_frame):
                for _, path in changes:
                    message = Message(
                        experiment_id="test_id",
                        local_path=Path(path).parent,
                        timestamp=datetime.now(),
                    )
                    queue.put_nowait(message)


if __name__ == "__main__":
    asyncio.run(main())
