from pathlib import Path
from uuid import UUID

from pydantic import BaseModel


class UploadDTO(BaseModel):

    timestep_id: UUID
    img_dir: Path
    bucket: str
    key: str
