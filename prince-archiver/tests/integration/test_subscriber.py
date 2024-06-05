import asyncio
from uuid import uuid4

import pytest
from aio_pika import Message, connect
from aio_pika.abc import AbstractExchange, AbstractIncomingMessage

from prince_archiver.data_archive.subscriber import ExchangeConfig, ManagedSubscriber


pytestmark = pytest.mark.integration


@pytest.fixture(name="exchange_config")
def fixture_exchange_config() -> ExchangeConfig:
    return ExchangeConfig(name=uuid4().hex)


@pytest.fixture(name="exchange")
async def fixture_exchange(exchange_config: ExchangeConfig):

    connection = await connect("amqp://guest:guest@localhost:5671")

    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(**exchange_config.__dict__)

        yield exchange


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


async def test_managed_subscriber(
    exchange: AbstractExchange,
    exchange_config: ExchangeConfig,
):
    message_handler = MessageHandler()

    subscriber = ManagedSubscriber(
        "amqp://guest:guest@localhost:5671",
        message_handler=message_handler,
        exchange_config=exchange_config,
    )
    async with subscriber:
        message_body = uuid4().hex.encode()

        await exchange.publish(Message(body=message_body), routing_key="misc")

        await message_handler.wait_for_message()
        assert message_body in message_handler.messages
