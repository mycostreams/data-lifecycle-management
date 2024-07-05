import logging
import os
import time
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile

import httpx
import redis

from .handler import Message
from .log import configure_logging

DATA_DIR = Path(__file__).parent / "data"
DATA_URL = "https://vu.data.surfsara.nl/index.php/s/74wJ36PdK7yToyM/download"


def get_timestep_data(target: Path | None = None):
    """Fetch example timestep data."""
    with (
        httpx.stream("GET", DATA_URL, timeout=120.0) as response,
        TemporaryDirectory() as _temp_dir,
    ):
        temp_file = Path(_temp_dir) / f"{uuid4().hex[:6]}.zip"
        with temp_file.open("wb") as file:
            for data in response.iter_bytes():
                file.write(data)

        with ZipFile(temp_file) as zip_file:
            zip_file.extractall(target or Path.cwd())


def main():
    configure_logging()

    data_dir = Path(os.getenv("DATA_DIR"))

    target_dir = data_dir / "test"
    if not target_dir.exists():
        logging.info("Fetching test data")
        target_dir.mkdir(parents=True)
        get_timestep_data(target_dir)

    redis_conn = redis.from_url(os.getenv("REDIS_DSN"))

    while True:
        msg = Message(
            experiment_id="test",
            local_path=(target_dir / "img").relative_to(data_dir),
            timestamp=datetime.now(),
        )

        logging.info("Publishing timestep...")
        redis_conn.publish("archiver:timestep", message=msg.model_dump_json())

        time.sleep(60)


if __name__ == "__main__":
    main()
