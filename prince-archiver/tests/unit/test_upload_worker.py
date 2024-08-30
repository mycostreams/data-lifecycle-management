from unittest.mock import AsyncMock

import pytest
from arq import Retry
from botocore.exceptions import ConnectTimeoutError

from prince_archiver.definitions import EventType
from prince_archiver.entrypoints.upload_worker.worker import workflow
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import ExportImagingEvent


@pytest.fixture(name="workflow_payload")
def fixture_workflow_payload():
    return {
        "ref_id": "8b5b871a23454f9bb22b2e6fbae51764",
        "experiment_id": "test_id",
        "timestamp": "2001-01-01T00:00:00+00:00",
        "type": EventType.STITCH,
        "local_path": "test/path",
    }


async def test_workflow_succesful(
    workflow_payload: dict,
):
    mock_messagebus = AsyncMock(MessageBus)
    ctx = {"messagebus": mock_messagebus}

    await workflow(ctx, workflow_payload)

    expected_msg = ExportImagingEvent(**workflow_payload)

    mock_messagebus.handle.assert_awaited_once_with(expected_msg)


@pytest.mark.parametrize("error_cls", (ConnectTimeoutError(endpoint_url="/"), OSError))
async def test_workflow_with_retries(workflow_payload: dict, error_cls: Exception):
    mock_messagebus = AsyncMock(MessageBus)
    mock_messagebus.handle.side_effect = error_cls

    ctx = {"messagebus": mock_messagebus}

    with pytest.raises(Retry):
        await workflow(ctx, workflow_payload)
