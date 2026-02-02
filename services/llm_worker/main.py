import asyncio
import logging
import sys
import os
import json

from .queue_manager import queue_manager
from .workflow import workflow_manager
from .config import settings
from .utils.logging_utils import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger("llm_worker")

async def worker_loop():
    logger.info("LLM worker started. Listening to queue: %s", settings.LLM_QUEUE)
    
    try:
        # Establish connection
        await queue_manager.connect()
        
        # Consume messages
        async for message in queue_manager.consume(settings.LLM_QUEUE):
            async with message.process():
                try:
                    task = json.loads(message.body)
                    logger.info("Task received: %s", task.get("chunk_id", "Unknown ID"))
                    await workflow_manager.pr_review_workflow(task)
                except Exception as e:
                    logger.exception("Error processing LLM task: %s", e)
                    # Automatically Nacked/Acked based on success/failure in block
                    
    except Exception as e:
        logger.critical("Critical LLM worker failure: %s", e)

if __name__ == "__main__":
    asyncio.run(worker_loop())
