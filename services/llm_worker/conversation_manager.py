import json
import redis
from .config import settings

class ConversationManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _get_key(self, review_request_id: str, chunk_id: str):
        return f"conversation:{review_request_id}:{chunk_id}"

    def fetch_conversation(self, review_request_id: str, chunk_id: str) -> list:
        key = self._get_key(review_request_id, chunk_id)
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return []
    
    def save_conversation(self, review_request_id: str, chunk_id: str, conversation: list):
        key = self._get_key(review_request_id, chunk_id)
        self.redis.set(key, json.dumps(conversation))

    def create_message(self, role: str, content: str) -> dict:
        return {"role": role, "content": content}

conversation_manager = ConversationManager()