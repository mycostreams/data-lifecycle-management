from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncGenerator

from fastapi import FastAPI

from prince_archiver.adapters.s3 import managed_file_system

from .dependencies import AppState, get_app_state
from .routes import router


@asynccontextmanager
async def lifespan(_: FastAPI, *, app_state: AppState) -> AsyncGenerator[None, None]:
    async with managed_file_system(app_state.file_system):
        yield


def create_app(*, _state: AppState | None = None):
    state = _state or get_app_state()

    app = FastAPI(
        lifespan=partial(lifespan, app_state=state),
    )

    app.include_router(router)

    @app.get("/health", response_model=None, status_code=204)
    async def health_check():
        """Get health check."""

    return app
