import asyncio
import os

import  redis.asyncio as redis


async def main():
    client = redis.from_url(
        os.getenv(
            "REDIS_DSN",
            "redis://localhost:6380",
        )
    )

    r = await client.ping()


if __name__ == "__main__":
    asyncio.run(main())