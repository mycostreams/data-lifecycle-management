from datetime import UTC, datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.api.deps import (
    get_file_system,
    get_session,
)
from prince_archiver.definitions import EventType
from prince_archiver.entrypoints.state_manager.app import create_app
from prince_archiver.entrypoints.state_manager.state import State


@pytest.fixture(name="client")
async def fixture_client(
    session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(_state=AsyncMock(State))

    file_system = AsyncMock()
    file_system._url.return_value = "http://test.com"

    app.dependency_overrides[get_file_system] = lambda: file_system
    app.dependency_overrides[get_session] = lambda: session

    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    async with client:
        yield client


async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 204


@pytest.mark.usefixtures("seed_data")
async def test_list_exports(client: AsyncClient):
    response = await client.get(
        "/api/1/exports",
        params={
            "start": datetime(1900, 1, 1, tzinfo=UTC),
        },
    )
    expected_response = {
        "count": 1,
        "data": [
            {
                "ref_id": "0b036a6a-5ba7-45ae-a242-90106014b08d",
                "experiment_id": "test_experiment_id",
                "timestamp": "2000-01-01T00:00:00Z",
                "type": "stitch",
                "url": "http://test.com/",
                "uploaded_at": "2001-01-01T00:00:00Z",
            }
        ],
    }
    assert response.json() == expected_response


@pytest.mark.usefixtures("seed_data")
@pytest.mark.usefixtures("seed_data")
@pytest.mark.parametrize(
    "filter_params,expected_count",
    (
        ({"start": datetime(1999, 1, 1, tzinfo=UTC)}, 1),
        ({"start": datetime(2010, 1, 1, tzinfo=UTC)}, 0),
        ({"event_type": EventType.STITCH}, 1),
        ({"event_type": EventType.VIDEO}, 0),
    ),
)
async def test_list_exports_filtering(
    client: AsyncClient, filter_params: dict, expected_count: int
):
    response = await client.get(
        "/api/1/exports",
        params={
            "start": datetime(1900, 1, 1, tzinfo=UTC),
            **filter_params,
        },
    )
    assert response.status_code == 200

    json_response: dict = response.json()
    assert json_response["count"] == expected_count


@pytest.mark.usefixtures("seed_data")
async def test_list_archives(client: AsyncClient):
    response = await client.get("/api/1/archives")

    assert response.status_code == 200

    expected_json = {
        "count": 1,
        "data": [
            {
                "id": "61159839-7745-466b-b78b-82f4c462fd6a",
                "path": "images/test_experiment_id/test.tar",
                "type": "stitch",
                "experiment_id": "test_experiment_id",
                "created_at": "2002-01-01T00:00:00Z",
                "member_count": 1,
                "url": "/api/1/archives/61159839-7745-466b-b78b-82f4c462fd6a",
            },
        ],
    }
    assert response.json() == expected_json


@pytest.mark.usefixtures("seed_data")
@pytest.mark.parametrize(
    "filter_params,expected_count",
    (
        ({"experiment_id": "test_experiment_id"}, 1),
        ({"experiment_id": "unknown_id"}, 0),
    ),
)
async def test_list_archives_filtering(
    client: AsyncClient,
    filter_params: dict,
    expected_count: int,
):
    response = await client.get(
        "/api/1/archives",
        params=filter_params,
    )
    json: dict = response.json()
    assert json["count"] == expected_count


@pytest.mark.usefixtures("seed_data")
async def test_read_archive(client: AsyncClient):
    response = await client.get("/api/1/archives/611598397745466bb78b82f4c462fd6a")

    assert response.status_code == 200

    expected_json = {
        "id": "61159839-7745-466b-b78b-82f4c462fd6a",
        "path": "images/test_experiment_id/test.tar",
        "type": "stitch",
        "experiment_id": "test_experiment_id",
        "created_at": "2002-01-01T00:00:00Z",
        "members": [
            {
                "member_key": "test_member_key",
                "ref_id": "0b036a6a-5ba7-45ae-a242-90106014b08d",
                "timestamp": "2000-01-01T00:00:00Z",
                "checksum": "test_hex",
                "size": 10,
            },
        ],
    }
    assert response.json() == expected_json


async def test_read_archive_not_found(client: AsyncClient):
    response = await client.get(f"/api/1/archives/{uuid4()}")
    assert response.status_code == 404
