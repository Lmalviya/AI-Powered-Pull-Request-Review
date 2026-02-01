import logging
import time
import functools
import uuid
from typing import Any, Callable

# Central Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("webhook_service")

def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to measure and log the execution time of a function.
    Useful for performance analysis.
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
            
    return wrapper

def generate_id() -> str:
    """Generate a unique review request ID."""
    return str(uuid.uuid4())
