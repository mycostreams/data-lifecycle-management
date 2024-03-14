from pathlib import Path

from image_stitcher.main import stitch_timestep
from image_stitcher.stitcher import Defaults, Stitcher
from image_stitcher.utils import resize_image

ROOT_DIR = Path(__file__).parent.parent


def main():

    defaults = Defaults(
        grid_size_x=2,
        grid_size_y=2,
    )

    stitcher = Stitcher(defaults=defaults)

    stitcher.run_stitch(
        src_dir=src_dir,
        target=target_path,
    )

    # target_dir = DATA_DIR / "resized"

    # imgs = []
    # for img in (DATA_DIR / "input").glob("*.tif"):
    #     resize_image(img, target_dir / img.name)

    # print("Hello")
    assert True
    # stitch_timestep(
    #     DATA_DIR / "input",
    #     DATA_DIR / "output" / "stitched.tif",
    # )


if __name__ == "__main__":
    main()
