from pathlib import Path

import cv2


def resize_image(
    source: Path,
    target: Path,
    scale_factor: float = 0.25,
):
    """Resize an image by a given scale factor."""
    image = cv2.imread(source.as_posix())
    small = cv2.resize(image, (0, 0), fx=scale_factor, fy=scale_factor)

    cv2.imwrite(target.as_posix(), small)
