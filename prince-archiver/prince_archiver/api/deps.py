from dataclasses import dataclass
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from s3fs import S3FileSystem
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

SessionmakerT = async_sessionmaker[AsyncSession]


@dataclass
class APIState:
    file_system: S3FileSystem
    sessionmaker: SessionmakerT


async def get_state(request: Request) -> APIState:
    state: APIState = request.state.state
    return state


async def get_file_system(
    state: Annotated[APIState, Depends(get_state)],
) -> S3FileSystem:
    return state.file_system


async def get_session(
    state: Annotated[APIState, Depends(get_state)],
) -> AsyncGenerator[AsyncSession, None]:
    async with state.sessionmaker() as session:
        yield session
