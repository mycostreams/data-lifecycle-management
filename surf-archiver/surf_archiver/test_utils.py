import threading
from dataclasses import dataclass
from typing import Optional

from pika import BlockingConnection, URLParameters
from pika.exchange_type import ExchangeType


class MessageWaiter:
    def __init__(self, *, _event: Optional[threading.Event] = None):
        self.event = _event or threading.Event()
        self.message: Optional[str] = None

    def set_message(self, message: str):
        self.message = message
        self.event.set()

    def wait(self):
        self.event.wait()


@dataclass
class SubscriberConfig:
    exchange: str
    connection_url: str
    exchange_type: ExchangeType = ExchangeType.fanout


class Subscriber:
    def __init__(
        self,
        config: SubscriberConfig,
        consume_event: Optional[threading.Event] = None,
    ):
        self.config = config

        parameters = URLParameters(self.config.connection_url)

        self.connection = BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange=self.config.exchange,
            exchange_type=self.config.exchange_type,
        )

        self.consume_event = consume_event or threading.Event()

    def consume(self, message_waiter: MessageWaiter, timeout: int = 3):
        result = self.channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue

        self.channel.queue_bind(exchange=self.config.exchange, queue=queue_name)
        self.channel.basic_qos(prefetch_count=1)

        consumer = self.channel.consume(
            queue_name,
            auto_ack=True,
            inactivity_timeout=timeout,
        )

        self.consume_event.set()

        for _, _, body in consumer:
            if isinstance(body, bytes):
                message_waiter.set_message(body.decode())
            self.channel.cancel()
