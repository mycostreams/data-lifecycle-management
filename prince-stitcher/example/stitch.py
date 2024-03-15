from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import httpx

from image_stitcher.main import stitch_timestep

DATA_DIR = Path(__file__).parent / "data"
DATA_URL = "https://vu.data.surfsara.nl/index.php/s/74wJ36PdK7yToyM/download"


def get_timestep_data(target: Path | None = None):
    """Fetch example timestep data."""
    with (
        httpx.stream("GET", DATA_URL) as response,
        NamedTemporaryFile() as temp_file,
    ):
        for data in response.iter_bytes():
            temp_file.write(data)

        with ZipFile(temp_file.name, "r") as zip_file:
            zip_file.extractall(target or Path.cwd())


def main():
    # fetch data if it doesn't already exist
    img_dir = DATA_DIR / "img"
    if not img_dir.exists():
        get_timestep_data(DATA_DIR)

    # Perform stitching
    stitch_timestep(dir=DATA_DIR / "img", target=DATA_DIR / "stitched.tif")


if __name__ == "__main__":
    main()
