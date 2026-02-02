import asyncio
import logging
import sys
import os

from .queue_manager import queue_manager
from .workflow import workflow_manager
from .config import settings
from .utils.logging_utils import setup_logging, get_logger
from .models import Action

# Configure logging
setup_logging()
logger = get_logger("orchestrator_worker")

async def worker_loop():
    logger.info("Git worker started. Listening to queue: %s", settings.GIT_QUEUE)
    
    while True:
        try:
            # Dequeue task from git_queue
            task = queue_manager.dequeue(settings.GIT_QUEUE)
            
            if not task:
                await asyncio.sleep(1)
                continue
            
            action = task.get("action")
            logger.info("Processing action: %s", action)
            
            if action == Action.GIT_COMMENT.value:
                await workflow_manager.git_inline_comment(task)
            elif action == Action.TOOL_CALL.value:
                await workflow_manager.tool_call(task)
            else:
                logger.warning("Unknown action received: %s", action)
                
        except Exception as e:
            logger.exception("Error in worker loop: %s", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(worker_loop())
