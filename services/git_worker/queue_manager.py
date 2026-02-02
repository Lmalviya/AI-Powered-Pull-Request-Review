import json
import asyncio
import aio_pika
import logging
from .config import settings

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.url = settings.RABBITMQ_URL
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
        await self.channel.declare_queue(queue_name, durable=True)
        
        message_body = json.dumps(payload).encode()
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self.channel.default_exchange.publish(
            message,
            routing_key=queue_name
        )

    async def consume(self, queue_name: str):
        if not self.channel or self.channel.is_closed:
            await self.connect()
            
        queue = await self.channel.declare_queue(queue_name, durable=True)
        # Set persistent prefetch count to 1 for fair dispatch
        await self.channel.set_qos(prefetch_count=1)
        
        # Return the async iterator
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                yield message

queue_manager = QueueManager()