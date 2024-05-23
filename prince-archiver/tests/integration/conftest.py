from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

CONNECTION_URL = "postgresql+asyncpg://postgres:postgres@localhost:5431/postgres"


@pytest.fixture(name="conn")
async def fixture_conn() -> AsyncGenerator[AsyncConnection, None]:
    engine = create_async_engine(CONNECTION_URL)
    async with engine.connect() as conn:
        yield conn


@pytest.fixture(name="sessionmaker")
async def fixture_sessionmaker(
    conn: AsyncConnection,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    async with conn.begin() as trans:
        sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=conn,
        )

        yield sessionmaker

        await trans.rollback()


@pytest.fixture(name="session")
async def fixture_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session
