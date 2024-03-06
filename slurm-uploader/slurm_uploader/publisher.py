from aio_pika import DeliveryMode, Message, connect

from .config import ExchangeConfig


async def publisher(
    connection_url: str,
    job_id: str,
    *,
    exchange_config: ExchangeConfig | None = None,
):
    exchange_config = exchange_config or ExchangeConfig()

    connection = await connect(connection_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_config.name,
            type=exchange_config.type,
        )

        message = Message(
            job_id.encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
        )

        await exchange.publish(message, routing_key=exchange_config.routing_key)
