from unittest.mock import AsyncMock

import pytest
from arq import Retry
from botocore.exceptions import ConnectTimeoutError

from prince_archiver.definitions import EventType, System
from prince_archiver.entrypoints.upload_worker.worker import State, run_export
from prince_archiver.service_layer.handlers.export import ExportHandler
from prince_archiver.service_layer.messages import ExportImagingEvent


@pytest.fixture(name="workflow_payload")
def fixture_workflow_payload():
    return {
        "ref_id": "8b5b871a23454f9bb22b2e6fbae51764",
        "experiment_id": "test_id",
        "timestamp": "2001-01-01T00:00:00+00:00",
        "type": EventType.STITCH,
        "system": System.PRINCE,
        "local_path": "test/path",
    }


async def test_run_export_successful(
    workflow_payload: dict,
):
    export_handler = AsyncMock()

    state = AsyncMock(State, export_handler=export_handler)
    ctx = {"state": state}

    await run_export(ctx, workflow_payload)

    expected_msg = ExportImagingEvent(**workflow_payload)

    export_handler.assert_awaited_once_with(expected_msg)


@pytest.mark.parametrize("error_cls", (ConnectTimeoutError(endpoint_url="/"), OSError))
async def test_workflow_with_retries(workflow_payload: dict, error_cls: Exception):
    export_handler = AsyncMock(ExportHandler)
    export_handler.side_effect = error_cls

    state = AsyncMock(State, export_handler=export_handler)
    ctx = {"state": state}

    with pytest.raises(Retry):
        await run_export(ctx, workflow_payload)
