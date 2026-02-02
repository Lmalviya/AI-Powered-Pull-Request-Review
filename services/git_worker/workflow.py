import redis
import logging
import json
import hashlib
from typing import Dict, Any, Optional
from .git_operations import gitlab_ops
from .git_operations import github_ops
from .models import ReviewRequest, Chunk, ChunkStatus
from .config import settings

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self):
        self.gitlab_ops = gitlab_ops.GitlabOps()
        self.github_ops = github_ops.GithubOps()
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_scm(self, provider: str):
        if provider == "gitlab":
            return self.gitlab_ops
        elif provider == "github":
            return self.github_ops
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def get_request_metadata(self, review_request_id: str):
        key = f"review_request:{review_request_id}"
        data = self.redis.get(key)
        if data:
            review_request = ReviewRequest.model_validate_json(data)
            return {
                "repo_id": review_request.repo_id,
                "pr_id": review_request.pr_id,
                "provider": review_request.provider
            }
        return None
    
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        key = f"chunk:{chunk_id}"
        data = self.redis.get(key)
        if data:
            return Chunk.model_validate_json(data)
        return None

    def update_chunk(self, chunk: Chunk):
        key = f"chunk:{chunk.chunk_id}"
        self.redis.set(key, chunk.model_dump_json())

    async def git_inline_comment(self, payload: Dict[str, Any]):
        """
        Posts an inline comment to GitHub/GitLab.
        """
        chunk_id = payload.get("chunk_id")
        if not chunk_id:
            logger.error("No chunk_id in payload")
            return

        chunk = self.get_chunk(chunk_id)
        if not chunk:
            logger.error(f"Chunk {chunk_id} not found")
            return

        # Optimization: Fetch ReviewRequest once
        rr_key = f"review_request:{chunk.review_request_id}"
        rr_data = self.redis.get(rr_key)
        if not rr_data:
            logger.error(f"Review request {chunk.review_request_id} not found")
            return
            
        review_request = ReviewRequest.model_validate_json(rr_data)
        
        repo_id = review_request.repo_id
        pr_id = review_request.pr_id
        provider = review_request.provider
        
        scm = self.get_scm(provider)

        # Idempotency Check
        if not chunk.comment_body or not chunk.filename or chunk.line_number is None:
            logger.warning(f"Chunk {chunk_id} missing comment data")
            chunk.status = ChunkStatus.FAILED
            self.update_chunk(chunk)
            return

        if not chunk.idempotency_hash:
            content_to_hash = f"{chunk.filename}:{chunk.line_number}:{chunk.comment_body}"
            chunk.idempotency_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

        # Check in Redis if this hash was already posted for this PR
        idempotency_key = f"posted:{repo_id}:{pr_id}:{chunk.idempotency_hash}"
        if self.redis.get(idempotency_key):
            logger.info(f"Comment already posted for chunk {chunk_id} (idempotency hit)")
            chunk.status = ChunkStatus.POSTED
            self.update_chunk(chunk)
            return

        try:
            commit_sha = review_request.metadata.get("head_sha")
            if not commit_sha:
                logger.error(f"head_sha missing for PR {repo_id}#{pr_id}")
                chunk.status = ChunkStatus.FAILED
                self.update_chunk(chunk)
                return

            success = scm.post_pr_comment(
                repo_id=repo_id,
                pr_id=pr_id,
                commit_sha=commit_sha,
                file=chunk.filename,
                line=chunk.line_number,
                body=chunk.comment_body
            )

            if success:
                chunk.status = ChunkStatus.POSTED
                # Mark as posted in Redis (TTL 24h to avoid leaks)
                self.redis.setex(idempotency_key, 86400, "1")
                logger.info(f"Successfully posted comment for chunk {chunk_id}")
            else:
                chunk.status = ChunkStatus.FAILED
                logger.error(f"Failed to post comment for chunk {chunk_id}")

        except Exception as e:
            logger.exception(f"Error posting comment for chunk {chunk_id}: {e}")
            chunk.status = ChunkStatus.FAILED
        
        self.update_chunk(chunk)

    def tool_call(self, payload: Dict[str, Any]):
        """
        Handles tool calls/context fetching.
        """
        chunk_id = payload.get("chunk_id")
        if not chunk_id:
            logger.error("No chunk_id in payload")
            return

        chunk = self.get_chunk(chunk_id)
        if not chunk:
            logger.error(f"Chunk {chunk_id} not found")
            return

        logger.info(f"Executing Tool Call for chunk {chunk_id}")
        
        # TODO: Implement actual tool execution/context fetching here.
        # This would likely involve checking chunk.metadata['tool_call'] 
        # and using scm to fetch symbols/files.
        
        # Simulate context fetched
        chunk.context_level += 1
        chunk.status = ChunkStatus.CONTEXT_READY
        self.update_chunk(chunk)
        
        # Enqueue back to Orchestrator for re-evaluation
        from .queue_manager import queue_manager
        queue_manager.enqueue(settings.ORCHESTRATOR_QUEUE, {
            "action": "EVALUATE_CHUNK", 
            "chunk_id": chunk_id
        })



workflow_manager = WorkflowManager()    