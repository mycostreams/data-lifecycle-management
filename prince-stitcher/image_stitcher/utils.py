from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np


class Dimensions(NamedTuple):
    x: int
    y: int


def resize_image(
    source: Path,
    target: Path,
    frame_size: Dimensions,
):
    """Resize an image by a given scale factor."""
    image = cv2.imread(source.as_posix())
    small = cv2.resize(image, frame_size)

    cv2.imwrite(target.as_posix(), small)


def write_blank_image(path: Path, frame_size: Dimensions):
    cv2.imwrite(
        path.as_posix(),
        np.zeros(frame_size),
        params=(cv2.IMWRITE_TIFF_COMPRESSION, 8),
    )
