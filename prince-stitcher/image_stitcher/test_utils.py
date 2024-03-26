import logging
import os
import shutil
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile

import httpx

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

    img_dir = Path(os.getenv("IMG_CACHE"))
    if not any(img_dir.iterdir()):
        logging.info("Fetching test data")
        get_timestep_data(img_dir)

    data_dir = Path(os.getenv("DATA_DIR"))
    while True:
        logging.info("Copying test data")
        shutil.copytree(img_dir, data_dir / uuid4().hex[:6])
        time.sleep(60)


if __name__ == "__main__":
    main()
