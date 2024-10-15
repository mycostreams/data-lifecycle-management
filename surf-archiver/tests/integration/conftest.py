import threading
from typing import Generator

import boto3
import pytest
from mypy_boto3_s3 import S3Client
from testcontainers.localstack import LocalStackContainer
from testcontainers.rabbitmq import RabbitMqContainer

from surf_archiver.test_utils import MessageWaiter, Subscriber, SubscriberConfig


@pytest.fixture(name="localstack", scope="session")
def fixture_localstack() -> Generator[LocalStackContainer, None, None]:
    localstack = LocalStackContainer("localstack/localstack:2.0.1").with_services("s3")
    localstack.region_name = None

    localstack.start()

    yield localstack

    localstack.stop()


@pytest.fixture(name="s3_endpoint_url", scope="session")
def fixture_s3_endpoint_url(localstack: LocalStackContainer) -> str:
    return localstack.get_url()


@pytest.fixture(scope="session", name="s3_client")
def fixture_s3_client(
    s3_endpoint_url: str,
) -> Generator[S3Client, None, None]:
    client = boto3.client(
        "s3",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        endpoint_url=s3_endpoint_url,
        region_name="us-west-1",
    )

    yield client

    client.close()


@pytest.fixture(scope="session", name="rabbitmq")
def fixture_rabbitmq() -> Generator[RabbitMqContainer, None, None]:
    rabbitmq = RabbitMqContainer()

    rabbitmq.start()

    yield rabbitmq

    rabbitmq.stop()


@pytest.fixture(name="connection_url")
def fixture_connection_url(rabbitmq: RabbitMqContainer) -> str:
    username = rabbitmq.username
    password = rabbitmq.password
    host = rabbitmq.get_container_host_ip()
    port = rabbitmq.get_exposed_port(rabbitmq.port)

    return f"amqp://{username}:{password}@{host}:{port}"


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
