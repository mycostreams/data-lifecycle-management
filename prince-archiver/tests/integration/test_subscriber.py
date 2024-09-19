import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from aio_pika import Message, connect
from aio_pika.abc import AbstractConnection, AbstractExchange, AbstractIncomingMessage
from testcontainers.rabbitmq import RabbitMqContainer

from prince_archiver.adapters.subscriber import ExchangeConfig, ManagedSubscriber

pytestmark = pytest.mark.integration


class MessageHandler:
    def __init__(self, event: asyncio.Event | None = None):
        self.messages = []
        self.event = asyncio.Event() or event

    async def __call__(self, message: AbstractIncomingMessage):
        async with message.process():
            self.messages.append(message.body)
            self.event.set()

    async def wait_for_message(self, timeout: int = 5):
        try:
            await asyncio.wait_for(self.event.wait(), timeout)
        except TimeoutError:
            pass


@pytest.fixture(name="rabbitmq_container", scope="module")
def fixture_rabbitmq_container() -> Generator[RabbitMqContainer, None, None]:
    with RabbitMqContainer() as container:
        yield container


@pytest.fixture(name="url")
def fixture_url(rabbitmq_container: RabbitMqContainer) -> str:
    username = rabbitmq_container.username
    password = rabbitmq_container.password
    host = rabbitmq_container.get_container_host_ip()
    port = rabbitmq_container.get_exposed_port(rabbitmq_container.port)

    return f"amqp://{username}:{password}@{host}:{port}"


@pytest.fixture(name="connection")
async def fixture_connection(
    url: str,
) -> AsyncGenerator[AbstractConnection, None]:
    connection = await connect(url)
    async with connection:
        yield connection


@pytest.fixture(name="exchange_config")
def fixture_exchange_config() -> ExchangeConfig:
    return ExchangeConfig(name=uuid4().hex)


@pytest.fixture(name="exchange")
async def fixture_exchange(
    exchange_config: ExchangeConfig,
    connection: AbstractConnection,
) -> AbstractExchange:
    channel = await connection.channel()
    exchange = await channel.declare_exchange(**exchange_config.__dict__)

    return exchange


async def test_managed_subscriber(
    url: str,
    exchange: AbstractExchange,
    exchange_config: ExchangeConfig,
):
    message_handler = MessageHandler()

    subscriber = ManagedSubscriber(
        url,
        message_handler=message_handler,
        exchange_config=exchange_config,
    )
    async with subscriber:
        message_body = uuid4().hex.encode()

        await exchange.publish(Message(body=message_body), routing_key="misc")

        await message_handler.wait_for_message()
        assert message_body in message_handler.messages
