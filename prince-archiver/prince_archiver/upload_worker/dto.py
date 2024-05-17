from uuid import UUID

from pydantic import BaseModel


class UploadDTO(BaseModel):

    timestep_id: UUID
    bucket: str
    key: str
