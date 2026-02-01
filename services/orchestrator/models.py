from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChunkStatus(str, Enum):
    PENDING = "PENDING"
    LLM_IN_PROGRESS = "LLM_IN_PROGRESS"
    TOOL_REQUIRED = "TOOL_REQUIRED"
    CONTEXT_READY = "CONTEXT_READY"
    COMMENT_READY = "COMMENT_READY"
    POSTED = "POSTED"
    FAILED = "FAILED"

class Chunk(BaseModel):
    chunk_id: str
    review_request_id: str
    diff_snippet: str
    context_level: int = 0
    status: ChunkStatus = ChunkStatus.PENDING
    filename: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewRequest(BaseModel):
    review_request_id: str
    repo_id: str
    pr_id: int
    provider: str = "github"
    status: str = "PENDING"
    created_at: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
