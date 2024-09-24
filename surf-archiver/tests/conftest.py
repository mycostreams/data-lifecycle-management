import threading
from typing import Generator
from uuid import uuid4

import pytest

from surf_archiver.test_utils import MessageWaiter, Subscriber, SubscriberConfig


@pytest.fixture(name="connection_url")
def fixture_connection_url() -> str:
    return "amqp://guest:guest@localhost:5671"


@pytest.fixture(name="random_str")
def fixture_random_str() -> str:
    return uuid4().hex


@pytest.fixture(name="message_waiter")
def fixture_message_waiter(
    connection_url: str,
    random_str: str,
) -> Generator[MessageWaiter, None, None]:
    def _target(message_waiter: MessageWaiter, consume_event: threading.Event):
        config = SubscriberConfig(
            connection_url=connection_url,
            exchange=random_str,
        )

        subscriber = Subscriber(config, consume_event)
        subscriber.consume(message_waiter, timeout=3)

    message_waiter = MessageWaiter()
    consume_event = threading.Event()

    thread = threading.Thread(target=_target, args=(message_waiter, consume_event))
    thread.start()

    consume_event.wait(timeout=2.0)

    yield message_waiter

    thread.join()
