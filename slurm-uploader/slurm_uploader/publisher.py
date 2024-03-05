import asyncio

import typer
from aio_pika import DeliveryMode, ExchangeType, Message, connect


async def publisher(connection_url: str, job_id: str):

    # Perform connection
    connection = await connect(connection_url)

    async with connection:

        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "slurm-uploader",
            ExchangeType.FANOUT,
        )

        message = Message(job_id, delivery_mode=DeliveryMode.PERSISTENT)

        await exchange.publish(message, routing_key="slurm-uploader")


def main(
    job_id: str,
    connection_url: str = "amqp://guest:guest@localhost/",
):
    asyncio.run(publisher(connection_url, job_id))


if __name__ == "__main__":
    typer.run(main)
