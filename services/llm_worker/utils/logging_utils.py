import logging
import time
import functools
import asyncio
from typing import Callable, Any

def setup_logging(level: int = logging.INFO):
    """
    Configures the root logger with a standard format.
    Should be called once at application startup.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger with the given name.
    """
    return logging.getLogger(name)

def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to measure and log the execution time of a function.
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        func_name = func.__name__
        logger = logging.getLogger(func.__module__)
        
        try:
            return await func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.info(f"Function '{func_name}' executed in {duration:.4f} seconds")
            
    return wrapper
