import asyncio
from datetime import date

from .client import ArchiveClientFactory
from .worker import Settings


async def main():
    settings = Settings()

    client_factory = ArchiveClientFactory(
        settings.USERNAME,
        settings.PASSWORD,
        settings.HOST,
    )

    async with client_factory.get_managed_client() as client:
        await client.archive(date.today())


if __name__ == "__main__":
    asyncio.run(main())
