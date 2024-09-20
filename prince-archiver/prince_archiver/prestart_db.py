import asyncio
import os

from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_fixed

from prince_archiver.service_layer.uow import get_session_maker


@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(5),
)
async def main():
    sessionmaker = get_session_maker(
        os.getenv(
            "POSTGRES_DSN",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        )
    )
    async with sessionmaker() as session:
        await session.execute(select(1))


if __name__ == "__main__":
    asyncio.run(main())
