import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple, Type

from ..git_operation.base_ops import BaseOps
from ..utils.hunk_processor import HunkProcessor
from ..utils.semantic_filter import SemanticFilter
from ..utils.logging_utils import get_logger, log_execution_time
from ..models import ReviewRequest, Chunk, ChunkStatus
from ..state import state_manager
from ..queue_manager import queue_manager
from .registry import ProviderRegistry
from .constants import ORCHESTRATOR_QUEUE, LLM_QUEUE, FAILED
from .pr_review_helpers import _fetch_pr_metadata, _process_single_file

logger = get_logger(__name__)

class WorkflowManager:
    """
    Orchestrates workflows and manages shared dependencies (DI Container pattern).
    """
    _scm_instances: Dict[str, BaseOps] = {}
    
    def __init__(self):
        # Service singletons
        self.hunk_processor = HunkProcessor()
        self.semantic_filter = SemanticFilter()

    @classmethod
    def get_scm(cls, provider_name: str) -> BaseOps:
        """Lazy-loads and checks cached SCM provider instances."""
        provider_key = provider_name.lower()
        if provider_key not in cls._scm_instances:
            scm_class = ProviderRegistry.get_scm_class(provider_key)
            cls._scm_instances[provider_key] = scm_class()
        return cls._scm_instances[provider_key]

    @log_execution_time
    async def pr_review_workflow(self, payload: Dict[str, Any]):
        """
        Main PR Review orchestration.
        """
        review_request_id = payload.get("review_request_id")
        provider = payload.get("provider", "github")
        repo_id = payload.get("repo")
        pr_id = payload.get("pr_number")

        logger.info(f"Starting review process for {provider} {repo_id}#{pr_id}")

        scm = self.get_scm(provider)
        
        # Init Review Request
        review_req = ReviewRequest(
            review_request_id=review_request_id,
            repo_id=repo_id,
            pr_id=pr_id,
            provider=provider,
            status="IN_PROGRESS",
            created_at=time.time()
        )
        state_manager.save_review_request(review_req)

        try:
            # Step 1: Fetch Diff & Metadata
            file_changes, (base_sha, head_sha) = await asyncio.gather(
                asyncio.to_thread(scm.get_pull_request_file_diffs, repo_id, pr_id),
                _fetch_pr_metadata(scm, repo_id, pr_id)
            )
            
            # Update metadata with SHAs
            review_req.metadata["base_sha"] = base_sha
            review_req.metadata["head_sha"] = head_sha
            state_manager.save_review_request(review_req)
        except Exception as e:
            logger.error(f"Failed to fetch PR data: {e}")
            review_req.status = FAILED
            state_manager.save_review_request(review_req)
            return

        # Step 2: Parallel File Processing
        tasks = [
            _process_single_file(fc, repo_id, base_sha, head_sha, self, scm, review_request_id)
            for fc in file_changes
        ]
        
        # Execute all file checks in parallel
        results = await asyncio.gather(*tasks)
        
        # Step 3: Enqueue Valid Chunks
        total_chunks = 0
        for file_chunks in results:
            for chunk in file_chunks:
                state_manager.save_chunk(chunk)
                await queue_manager.enqueue(ORCHESTRATOR_QUEUE, {
                    "action": "EVALUATE_CHUNK",
                    "chunk_id": chunk.chunk_id
                })
                total_chunks += 1

        logger.info(f"Initialized review {review_request_id} with {total_chunks} chunks.")
        
        if total_chunks == 0:
            review_req.status = "COMPLETED"
            review_req.metadata["reason"] = "No reviewable changes found"
            state_manager.save_review_request(review_req)

    @log_execution_time
    async def evaluate_chunk(self, payload: Dict[str, Any]):
        """
        EVALUATE_CHUNK
        if status == PENDING or CONTEXT_READY:
            status = LLM_IN_PROGRESS
            enqueue LLM_CALL(chunk_id)
        """
        chunk_id = payload.get("chunk_id")
        chunk = state_manager.get_chunk(chunk_id)
        
        if not chunk:
            logger.error(f"Chunk {chunk_id} not found")
            return

        # Enforce valid state transitions
        if chunk.status in [ChunkStatus.PENDING, ChunkStatus.CONTEXT_READY]:
            chunk.status = ChunkStatus.LLM_IN_PROGRESS
            state_manager.save_chunk(chunk)
            
            # Enqueue to LLM Queue
            await queue_manager.enqueue(LLM_QUEUE, {
                "chunk_id": chunk_id,
                "review_request_id": chunk.review_request_id,
                "diff_snippet": chunk.diff_snippet,
                "filename": chunk.filename,
                "context_level": chunk.context_level
            })
            logger.info(f"Chunk {chunk_id} enqueued to LLM_QUEUE")
        else:
            logger.info(f"Chunk {chunk_id} in status {chunk.status}, skipping EVALUATE_CHUNK")


# Global instance
workflow_manager = WorkflowManager()
