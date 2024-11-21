import logging
from contextlib import AsyncExitStack, asynccontextmanager
from functools import partial
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI

from prince_archiver.adapters.s3 import managed_file_system
from prince_archiver.api import router
from prince_archiver.models import init_mappers

from .state import State, get_state

LOGGER = logging.getLogger(__name__)


class AppState(TypedDict):
    state: State


@asynccontextmanager
async def lifespan(_: FastAPI, *, state: State) -> AsyncIterator[AppState]:
    init_mappers()

    LOGGER.info("Starting up")

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(state.redis)
        await stack.enter_async_context(managed_file_system(state.file_system))

        # Consumers
        await stack.enter_async_context(state.import_ingester.managed_consumer())
        await stack.enter_async_context(state.export_ingester.managed_consumer())
        await stack.enter_async_context(state.subscriber)

        yield {"state": state}

        state.stop_event.set()


def create_app(*, _state: State | None = None):
    state = _state or get_state()

    app = FastAPI(
        lifespan=partial(lifespan, state=state),
    )

    app.include_router(router)

    @app.get("/health", response_model=None, status_code=204)
    async def health_check():
        """Get health check."""

    return app
