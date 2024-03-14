import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar

import imagej
from pydantic import BaseModel, Field


@dataclass
class Defaults:
    """Configurable options for ImageJ plugin"""

    grid_size_x: int = 15
    grid_size_y: int = 10
    grid_size_z: int = 1
    overlap: int = 20
    file_names: str = "Img_r{yy}_c{xx}.tif"
    rgb_order: str = "rgb"
    output_file_name: str = "registered.txt"
    save_only_tile_config: bool = False
    start_x: int = 1
    start_y: int = 1
    start_z: int = 1
    start_i: int = 1
    channels_for_registration: str = "Red, Green and Blue"
    fusion_method: str = "Linear Blending"
    fusion_alpha: float = 1.0
    regression_threshold: float = 0.1
    avg_displacement_threshold: int = 6
    absolute_displacement_threshold: int = 6


class _PluginParams(BaseModel):
    """Params to be passed into ImageJ plugin.

    Note: Order for plugin is highly important

    """

    PLUGIN: ClassVar[str] = "Stitch Sequence of Grids of Images"

    grid_size_x: int
    grid_size_y: int
    grid_size_z: int
    overlap: int
    input_dir: Path = Field(..., serialization_alias="input")
    file_names: str
    rgb_order: str
    output_file_name: str
    output_dir: Path = Field(..., serialization_alias="output")
    save_only_tile_config: bool = Field(
        ...,
        serialization_alias="Save_Only_Tile_Configuration",
    )
    start_x: int
    start_y: int
    start_z: int
    start_i: int
    channels_for_registration: str
    fusion_method: str
    fusion_alpha: float
    regression_threshold: float
    avg_displacement_threshold: int
    absolute_displacement_threshold: int


class AbstractStitcher(ABC):

    @abstractmethod
    def run_stitch(params, src_dir: Path, target: Path): ...


class Stitcher(AbstractStitcher):

    def __init__(
        self,
        defaults: Defaults | None = None,
        fiji_home: str | None = None,
    ):
        self.defaults = defaults or Defaults()
        self.ij = imagej.init(fiji_home or os.getenv("FIJI_HOME", "Fiji.app"))

    def run_stitch(self, src_dir: Path, target: Path):
        with TemporaryDirectory() as _temp_dir:
            temp_dir = Path(_temp_dir)

            plugin_params = _PluginParams(
                input_dir=src_dir,
                output_dir=temp_dir,
                **self.defaults.__dict__,
            )

            self.ij.py.run_plugin(
                plugin_params.PLUGIN,
                plugin_params.model_dump(mode="json", by_alias=True),
            )

            # Move the stitched image to the target directory
            stitched_image = next(temp_dir.iterdir())
            stitched_image.rename(target)
