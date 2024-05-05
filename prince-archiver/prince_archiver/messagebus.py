from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Generic, Mapping, TypeVar

from pydantic import BaseModel

from .db import AbstractUnitOfWork

ModelT = TypeVar("ModelT", bound=BaseModel)

HandlerMappingT = Mapping[
    type[BaseModel],
    list[Callable, Awaitable[None]],
]


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
        messages = [message]
        while messages:
            message = messages.pop()
            for handler in self.handlers[message.__class__]:
                await handler(message, self.uow)
