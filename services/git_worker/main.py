import asyncio
import logging
import sys
import os
import json

from .queue_manager import queue_manager
from .workflow import workflow_manager
from .config import settings
from .utils.logging_utils import setup_logging, get_logger
from .models import Action

# Configure logging
setup_logging()
logger = get_logger("git_worker")

async def worker_loop():
    logger.info("Git worker started. Listening to queue: %s", settings.GIT_QUEUE)
    
    try:
        # Establish connection
        await queue_manager.connect()
        
        # Consume messages
        async for message in queue_manager.consume(settings.GIT_QUEUE):
            async with message.process():
                try:
                    task = json.loads(message.body)
                    action = task.get("action")
                    logger.info("Processing action: %s", action)
                    
                    if action == Action.GIT_COMMENT.value:
                        await workflow_manager.git_inline_comment(task)
                    elif action == Action.TOOL_CALL.value:
                        await workflow_manager.tool_call(task)
                    else:
                        logger.warning("Unknown action received: %s", action)
                        # Implicit Ack via message.process() closure
                        
                except Exception as e:
                    logger.exception("Error processing Git task: %s", e)
                    # Implicit Nack (or Ack if handled, depending on policy). 
                    # aio_pika's message.process(requeue=True/False) handles this. 
                    # Default is to Nack without requeue if error propagates? 
                    # Actually standard process context manager behavior:
                    # If exception -> Nack (requeue=True by default in some versions, False in others, let's trust default or handle manually if needed).
                    # For safety, let's catch criticals.
                    
    except Exception as e:
        logger.critical("Critical Git worker failure: %s", e)

if __name__ == "__main__":
    asyncio.run(worker_loop())
