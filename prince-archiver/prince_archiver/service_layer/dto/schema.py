from typing import Literal

from pydantic import BaseModel

from .common import CommonImagingEvent, Metadata


# Schemas for writing to file
class BaseSchema(BaseModel):
    pass


class Schema(CommonImagingEvent, BaseSchema):
    schema_version: Literal["1a0"] = "1a0"
    metadata: Metadata
