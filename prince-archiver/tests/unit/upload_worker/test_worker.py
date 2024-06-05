from pathlib import Path
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from prince_archiver.config import WorkerSettings
from prince_archiver.messagebus import MessageBus
from prince_archiver.upload_worker.dto import UploadDTO
from prince_archiver.upload_worker.worker import workflow


@pytest.fixture(name="upload_worker_settings")
def fixture_upload_worker_settings() -> WorkerSettings:
    return WorkerSettings(
        REDIS_DSN="redis://test:6379",
        POSTGRES_DSN="postgresql+asyncpg://test:test@test-db:5432/test",
        AWS_ACCESS_KEY_ID="test-key",
        AWS_SECRET_ACCESS_KEY="test-secret-key",
        AWS_BUCKET_NAME="test-bucket",
        DATA_DIR=Path("/root"),
    )


@pytest.fixture(name="workflow_payload")
def fixture_workflow_payload():
    return {
        "timestep_id": "8b5b871a23454f9bb22b2e6fbae51764",
        "plate": 1,
        "cross_date": "2000-01-01",
        "position": 1,
        "timestamp": "2001-01-01T00:00:00+00:00",
        "image_count": 1,
        "path": "test/path",
    }


async def test_workflow(
    upload_worker_settings: WorkerSettings,
    workflow_payload: dict,
):

    mock_messagebus = AsyncMock(MessageBus)
    ctx = {
        "settings": upload_worker_settings,
        "messagebus": mock_messagebus,
    }

    await workflow(ctx, workflow_payload)

    expected_message = UploadDTO(
        timestep_id=UUID("8b5b871a23454f9bb22b2e6fbae51764"),
        img_dir=Path("/root/test/path"),
        key="20000101_001/20010101_0000.tar",
        bucket="test-bucket",
    )

    mock_messagebus.handle.assert_awaited_once_with(expected_message)
