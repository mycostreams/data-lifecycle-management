from textwrap import dedent
from typing import AsyncGenerator

import pytest

from surf_archiver.publisher import (
    BaseMessage,
    ManagedPublisher,
    PublisherConfig,
    _Publisher,
)
from surf_archiver.test_utils import MessageWaiter


@pytest.fixture(name="publisher")
async def fixture_publisher(
    connection_url: str,
    random_str: str,
) -> AsyncGenerator[_Publisher, None]:
    config = PublisherConfig(
        connection_url=connection_url,
        exchange_name=random_str,
    )

    async with ManagedPublisher(config) as publisher:
        yield publisher


async def test_publisher(
    publisher: _Publisher,
    message_waiter: MessageWaiter,
):
    class Message(BaseMessage):
        test_field: str = "test"

    await publisher.publish(Message())

    expected_message = dedent(
        """\
        {
            "test_field": "test"
        }
        """
    )

    message_waiter.wait()
    assert message_waiter.message == expected_message.strip()
