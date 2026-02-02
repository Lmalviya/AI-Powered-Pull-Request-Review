import json
import logging
import redis
from .conversation_manager import conversation_manager
from .llms.factory import get_llm_client
from .prompts.prompt_builder import prompt_builder
from .models import Chunk, ChunkStatus, Action
from .config import settings
from .queue_manager import queue_manager

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self):
        self.llm = get_llm_client()
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _get_chunk(self, chunk_id: str) -> Chunk:
        data = self.redis.get(f"chunk:{chunk_id}")
        if data:
            return Chunk.model_validate_json(data)
        return None

    def _update_chunk(self, chunk: Chunk):
        self.redis.set(f"chunk:{chunk.chunk_id}", chunk.model_dump_json())

    async def pr_review_workflow(self, payload: dict):
        chunk_id = payload.get("chunk_id")
        if not chunk_id:
            logger.error("No chunk_id in payload")
            return

        chunk = self._get_chunk(chunk_id)
        if not chunk:
            logger.error(f"Chunk {chunk_id} not found")
            return

        logger.info(f"LLM Worker processing chunk {chunk_id} (context_level={chunk.context_level})")

        # 1. Load Conversation
        conversation = conversation_manager.fetch_conversation(
            chunk.review_request_id, chunk_id
        )

        # Optimization: Need repo/pr info for prompt
        # We can fetch this once if conversation is empty
        repo_id = "unknown"
        pr_id = "unknown"
        
        if not conversation:
            from .models import ReviewRequest 
            rr_data = self.redis.get(f"review_request:{chunk.review_request_id}")
            if rr_data:
                # We need a ReviewRequest model in llm_worker/models.py to parse this cleanly
                # Or just use json.loads since we only need fields.
                # Let's verify models.py has ReviewRequest
                rr = json.loads(rr_data)
                repo_id = rr.get("repo_id")
                pr_id = rr.get("pr_id")

        # 2. Add New Message based on Context
        if not conversation:
            # Initial review
            conversation = prompt_builder.build_initial_messages(chunk.model_dump(), repo_id, pr_id)
        elif chunk.status == ChunkStatus.CONTEXT_READY:
            # Re-evaluating after tool call
            # Assuming metadata contains the tool output
            context_msg = prompt_builder.build_context_message({
                "tool": chunk.metadata.get("last_tool"),
                "content": chunk.metadata.get("tool_output", "No content found")
            })
            conversation.append(context_msg)
        
        # 3. Call LLM
        try:
            chunk.status = ChunkStatus.LLM_IN_PROGRESS
            self._update_chunk(chunk)

            response_text = self.llm.generate_response(conversation)
            llm_result = json.loads(response_text)
            
            # Save assistant response to history
            conversation.append(conversation_manager.create_message("assistant", response_text))
            conversation_manager.save_conversation(chunk.review_request_id, chunk_id, conversation)

            # 4. Parse Result & Route
            model_type = llm_result.get("model") # 'answer' or 'tool'
            
            if model_type == "tool":
                tool_call = llm_result.get("tool_call", {})
                chunk.status = ChunkStatus.TOOL_REQUIRED
                chunk.metadata["last_tool"] = tool_call.get("tool")
                chunk.metadata["tool_args"] = tool_call.get("args")
                self._update_chunk(chunk)
                
                # Enqueue to GIT_QUEUE for tool execution
                await queue_manager.enqueue(settings.GIT_QUEUE, {
                    "action": Action.TOOL_CALL.value,
                    "chunk_id": chunk_id
                })
                logger.info(f"Chunk {chunk_id} needs tool call: {chunk.metadata['last_tool']}")

            elif model_type == "answer":
                comments = llm_result.get("content", [])
                if comments:
                    # For now, we only handle the first comment as per git_worker current structure
                    # Ideally, we should loop or handle multiple.
                    # Fixing for current git_worker flow:
                    main_comment = comments[0]
                    chunk.comment_body = main_comment.get("comment")
                    chunk.line_number = main_comment.get("line")
                    chunk.status = ChunkStatus.COMMENT_READY
                    self._update_chunk(chunk)
                    
                    await queue_manager.enqueue(settings.GIT_QUEUE, {
                        "action": Action.GIT_COMMENT.value,
                        "chunk_id": chunk_id
                    })
                    logger.info(f"Chunk {chunk_id} generated comment on line {chunk.line_number}")
                else:
                    chunk.status = ChunkStatus.COMPLETED
                    self._update_chunk(chunk)
                    logger.info(f"Chunk {chunk_id} completed (no issues)")

        except Exception as e:
            logger.exception(f"Error in LLM workflow for chunk {chunk_id}: {e}")
            chunk.status = ChunkStatus.FAILED
            self._update_chunk(chunk)

workflow_manager = WorkflowManager()