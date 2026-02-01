import uuid
import asyncio
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING

from ..models import Chunk, ChunkStatus
from ..utils.filter_utils import should_review_file
from ..utils.logging_utils import get_logger
from ..git_operation.base_ops import BaseOps

if TYPE_CHECKING:
    from .manager import WorkflowManager

logger = get_logger(__name__)

async def _fetch_pr_metadata(scm: BaseOps, repo_id: str, pr_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Fetches base and head SHAs for the PR."""
    try:
        pr_data = await asyncio.to_thread(scm.get_pull_request, repo_id, pr_id)
        return pr_data.get("base", {}).get("sha"), pr_data.get("head", {}).get("sha")
    except Exception as e:
        logger.warning(f"[PR #{pr_id}] Failed to fetch metadata: {e}")
        return None, None

async def _process_single_file(
    fc: Dict[str, Any],
    repo_id: str,
    base_sha: Optional[str],
    head_sha: Optional[str],
    manager: 'WorkflowManager',
    scm: BaseOps,
    review_request_id: str
) -> List[Chunk]:
    """
    Processes a single file change:
    1. Checks if file is relevant (extension)
    2. checks if changes are semantic
    3. chunks the diff
    """
    filename = fc.get("filename")
    patch = fc.get("patch")

    # 1. Relevancy Check
    if not patch or not should_review_file(filename):
        return []

    # 2. Semantic Check
    if base_sha and head_sha:
        try:
            old_content = await asyncio.to_thread(scm.get_file_content, repo_id, filename, ref=base_sha)
            new_content = await asyncio.to_thread(scm.get_file_content, repo_id, filename, ref=head_sha)
            
            if not manager.semantic_filter.is_semantic_change(old_content, new_content, filename):
                logger.info(f"Skipping {filename}: Non-semantic change.")
                return []
        except Exception as e:
            logger.warning(f"Semantic check failed for {filename}, proceeding: {e}")

    # 3. Chunking
    chunks = []
    try:
        hunks = list(manager.hunk_processor.chunk_patch(filename, patch))
        for c_data in hunks:
            chunk = Chunk(
                chunk_id=str(uuid.uuid4()),
                review_request_id=review_request_id,
                filename=filename,
                diff_snippet=c_data["content"],
                status=ChunkStatus.PENDING,
                metadata={
                    "start_line": c_data["start_line"],
                    "end_line": c_data["end_line"]
                }
            )
            chunks.append(chunk)
    except Exception as e:
        logger.error(f"Error chunking {filename}: {e}")
    
    return chunks
