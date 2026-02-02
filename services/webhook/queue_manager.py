import json
import asyncio
import aio_pika
from .config import settings
from .utils import logger

class QueueManager:
    def __init__(self):
        self.url = settings.rabbitmq_url
        self.connection = None
        self.channel = None

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                logger.info("Connected to RabbitMQ")
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise e

    async def enqueue(self, queue_name: str, payload: dict):
        if not self.channel or self.channel.is_closed:
            await self.connect()

        # Ensure queue exists
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        message_body = json.dumps(payload).encode()
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self.channel.default_exchange.publish(
            message,
            routing_key=queue_name
        )

queue_manager = QueueManager()
