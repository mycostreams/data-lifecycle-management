from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.uow import AbstractUnitOfWork


class MockMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)


class MockHandler:
    def __init__(self):
        self.processed_messages: list[MockMessage] = []

    async def __call__(self, message: MockMessage, _: AbstractUnitOfWork):
        self.processed_messages.append(message)


async def test_messagebus_handler():
    first_message = MockMessage()
    second_message = MockMessage()

    mock_handler = MockHandler()

    uow = AsyncMock(AbstractUnitOfWork)
    uow.collect_messages.return_value = iter([second_message])

    messagebus = MessageBus(handlers={MockMessage: [mock_handler]}, uow=uow)

    await messagebus.handle(first_message)

    assert mock_handler.processed_messages == [first_message, second_message]
