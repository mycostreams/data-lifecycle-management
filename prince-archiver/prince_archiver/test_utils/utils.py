from pathlib import Path
from shutil import copy
from timeit import default_timer


class Timer:
    def __init__(self):
        self.ref = default_timer()

    @property
    def delta(self) -> float:
        return default_timer() - self.ref


def make_timestep_directory(target_dir: Path, src_img: Path) -> None:
    """Construct a new timestep directory."""
    target_dir.mkdir(parents=True, exist_ok=True)

    img = target_dir / "Img_r10_c15.tif"
    copy(src_img, img)
