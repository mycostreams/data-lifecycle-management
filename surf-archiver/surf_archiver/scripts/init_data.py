import asyncio
import os

from surf_archiver.file import managed_s3_file_system


async def main():
    """Populate S3 with test data.

    This is intended for development purposes only.
    """
    async with managed_s3_file_system() as s3:
        bucket = os.getenv(
            "SURF_ARCHVIER_BUCKET",
            "mycostreams-raw-data",
        )

        await s3._makedirs(bucket, exist_ok=True)

        keys = (
            f"{bucket}/images/test-id/20000101/{index:02}00.tar" for index in range(5)
        )
        await asyncio.gather(*[s3._pipe(key, b"\x01" * 1024) for key in keys])


if __name__ == "__main__":
    asyncio.run(main())
