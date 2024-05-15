from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field

from prince_archiver.utils import now


class UploadDTO(BaseModel):

    timestep_id: UUID
    bucket: str
    key: str
