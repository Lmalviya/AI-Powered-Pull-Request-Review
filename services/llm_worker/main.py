import asyncio
import logging
import sys
import os

from .queue_manager import queue_manager
from .workflow import workflow_manager
from .config import settings
from .utils.logging_utils import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger("llm_worker")

async def worker_loop():
    logger.info("LLM worker started. Listening to queue: %s", settings.LLM_QUEUE)
    
    while True:
        try:
            # Dequeue task from LLM_QUEUE
            task = queue_manager.dequeue(settings.LLM_QUEUE)
            
            if not task:
                await asyncio.sleep(1)
                continue
            
            # The orchestrator sends the chunk_id in the payload
            logger.info("Task received: %s", task)
            await workflow_manager.pr_review_workflow(task)
            
        except Exception as e:
            logger.exception("Error in LLM worker loop: %s", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(worker_loop())
