from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncGenerator

from fastapi import FastAPI

from .dependencies import AppState, get_app_state
from .routes import router


@asynccontextmanager
async def lifespan(_: FastAPI, *, app_state: AppState) -> AsyncGenerator[None, None]:
    session = await app_state.file_system.set_session()

    yield

    await session.close()


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


app = create_app()
