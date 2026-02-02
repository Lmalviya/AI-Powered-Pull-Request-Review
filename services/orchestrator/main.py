import asyncio
import logging
import sys
import os
import json

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
    
    try:
        # Establish initial connection
        await queue_manager.connect()
        
        # Consume messages using async iterator
        async for message in queue_manager.consume(settings.ORCHESTRATOR_QUEUE):
            async with message.process():
                try:
                    task = json.loads(message.body)
                    action = task.get("action")
                    logger.info("Processing action: %s", action)
                    
                    if action == Action.START_PR_REVIEW.value:
                        await workflow_manager.pr_review_workflow(task)
                    elif action == Action.EVALUATE_CHUNK.value:
                        await workflow_manager.evaluate_chunk(task)
                    else:
                        logger.warning("Unknown action received: %s", action)
                        # We still ack unknown actions to remove them from queue
                        
                except Exception as e:
                    logger.exception("Error processing message: %s", e)
                    
    except Exception as e:
        logger.critical("Critical worker failure: %s", e)
        # Restart logic or let docker restart container

if __name__ == "__main__":
    asyncio.run(worker_loop())
