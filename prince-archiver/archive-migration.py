
import os
import logging
import asyncio

from sqlalchemy import select

from prince_archiver.models.write import DataArchiveEntry
from prince_archiver.service_layer.uow import get_session_maker


logging.basicConfig(level=logging.INFO)


async def main():
    logging.info("Migrating data")



    sessionmaker = get_session_maker(
        os.getenv(
            "POSTGRES_DSN", 
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        )
    )

    async with sessionmaker() as session:
        result = await session.stream_scalars(
            select(DataArchiveEntry)
            .where(~DataArchiveEntry.path.startswith("images/"))
        )

        async for item in result:
            item.path = f"images/{item.path}"
        await session.commit()
    
    logging.info("Migration complete")


if __name__ == "__main__":
    asyncio.run(main())
