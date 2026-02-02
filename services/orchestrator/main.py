import asyncio
import logging
import sys
import os

from .queue_manager import queue_manager
from .workflows import workflow_manager
from .config import settings
from .utils.logging_utils import setup_logging, get_logger
from .models import Action

# Configure logging
setup_logging()
logger = get_logger("orchestrator_worker")

async def worker_loop():
    logger.info("Orchestrator worker started. Listening to queue: %s", settings.ORCHESTRATOR_QUEUE)
    
    while True:
        try:
            # Dequeue task from orchestrator_queue
            task = queue_manager.dequeue(settings.ORCHESTRATOR_QUEUE)
            
            if not task:
                await asyncio.sleep(1)
                continue
            
            action = task.get("action")
            logger.info("Processing action: %s", action)
            
            if action == Action.START_PR_REVIEW.value:
                await workflow_manager.pr_review_workflow(task)
            elif action == Action.EVALUATE_CHUNK.value:
                await workflow_manager.evaluate_chunk(task)
            else:
                logger.warning("Unknown action received: %s", action)
                
        except Exception as e:
            logger.exception("Error in worker loop: %s", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(worker_loop())
