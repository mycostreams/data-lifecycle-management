from pathlib import Path
from typing import NamedTuple

import cv2


class Dimensions(NamedTuple):
    x: int
    y: int


def resize_image(
    source: Path,
    target: Path,
    dimensions: Dimensions,
):
    """Resize an image by a given scale factor."""
    image = cv2.imread(source.as_posix())
    small = cv2.resize(image, dimensions)

    cv2.imwrite(target.as_posix(), small)
