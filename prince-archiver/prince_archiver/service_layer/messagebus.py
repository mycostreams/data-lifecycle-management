from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Generic, Mapping, TypeVar

from pydantic import BaseModel

from prince_archiver.service_layer.uow import AbstractUnitOfWork

ModelT = TypeVar("ModelT", bound=BaseModel)

HandlerMappingT = Mapping[
    type[BaseModel],
    list[Callable[..., Awaitable[None]]],
]

MessagebusFactoryT = Callable[[], "MessageBus"]


class AbstractHandler(Generic[ModelT], ABC):
    @abstractmethod
    async def __call__(self, message: ModelT, uow: AbstractUnitOfWork): ...


class MessageBus:
    def __init__(
        self,
        handlers: HandlerMappingT,
        uow: AbstractUnitOfWork,
    ):
        self.handlers = handlers
        self.uow = uow

    async def handle(self, message: BaseModel):
        messages: list[BaseModel] = [message]
        while messages:
            message = messages.pop()
            for handler in self.handlers.get(message.__class__, []):
                await handler(message, self.uow)
                for message in self.uow.collect_messages():
                    messages.append(message)

    @classmethod
    def factory(
        cls,
        handlers: HandlerMappingT,
        uow: Callable[[], AbstractUnitOfWork],
    ) -> MessagebusFactoryT:
        return lambda: cls(handlers, uow())
