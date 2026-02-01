import json
import redis
from typing import Optional, List, Dict, Any
from .config import settings
from .models import Chunk, ReviewRequest

class StateManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def save_review_request(self, request: ReviewRequest):
        key = f"review_request:{request.review_request_id}"
        self.redis.set(key, request.model_dump_json())

    def get_review_request(self, review_request_id: str) -> Optional[ReviewRequest]:
        key = f"review_request:{review_request_id}"
        data = self.redis.get(key)
        if data:
            return ReviewRequest.model_validate_json(data)
        return None

    def save_chunk(self, chunk: Chunk):
        key = f"chunk:{chunk.chunk_id}"
        self.redis.set(key, chunk.model_dump_json())
        # Also add to a set for the review request
        self.redis.sadd(f"review_request_chunks:{chunk.review_request_id}", chunk.chunk_id)

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        key = f"chunk:{chunk_id}"
        data = self.redis.get(key)
        if data:
            return Chunk.model_validate_json(data)
        return None

    def get_chunks_for_request(self, review_request_id: str) -> List[Chunk]:
        chunk_ids = self.redis.smembers(f"review_request_chunks:{review_request_id}")
        chunks = []
        for cid in chunk_ids:
            chunk = self.get_chunk(cid)
            if chunk:
                chunks.append(chunk)
        return chunks

state_manager = StateManager()
