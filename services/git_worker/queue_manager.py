import json
import redis
from .config import settings

class QueueManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def enqueue(self, queue_name: str, payload: dict):
        self.redis.lpush(queue_name, json.dumps(payload))

    def dequeue(self, queue_name: str, timeout: int = 5):
        data = self.redis.brpop(queue_name, timeout=timeout)
        if data:
            return json.loads(data[1])
        return None

queue_manager = QueueManager()