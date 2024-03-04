from pathlib import Path

from watchfiles import Change


def filter_on_final_image(change: Change, path: str) -> bool:
    return change == Change.added and Path(path).name == "Img_r10_c15.tif"
