from functools import lru_cache
from pathlib import Path
from shutil import copy
from timeit import default_timer

import httpx

from prince_archiver.service_layer.external_dto import TimestepMeta

DOWNLOAD_URL = "https://vu.data.surfsara.nl/index.php/s/ndI1UoMRwliVYGR/download"


class Timer:
    def __init__(self):
        self.ref = default_timer()

    @property
    def delta(self) -> float:
        return default_timer() - self.ref


@lru_cache
def _get_image(url: str = DOWNLOAD_URL):
    response = httpx.get(url)
    return response.content


def make_timestep_directory(
    meta: TimestepMeta,
    base_dir: Path,
    src_img: Path | None = None,
) -> None:
    """Construct a new timestep directory."""
    img_dir = base_dir / meta.system / meta.img_dir
    img_dir.mkdir(parents=True, exist_ok=True)

    img = img_dir / "Img_r10_c15.tif"
    if src_img:
        copy(src_img, img)
    else:
        img.write_bytes(_get_image())

    events_dir = base_dir / meta.system / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    event_file = events_dir / f"{meta.timestamp.timestamp():.0f}.json"
    event_file.write_text(meta.model_dump_json(indent=4, by_alias=True))
