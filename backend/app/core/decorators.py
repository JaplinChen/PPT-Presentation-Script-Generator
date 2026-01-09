import functools
import logging
import asyncio
from typing import Callable, Any

logger = logging.getLogger(__name__)

def async_task_handler(task_name: str = "Unknown Task"):
    """
    Decorator for async background tasks to standardize error handling and logging.
    
    Args:
        task_name (str): Human-readable name of the task.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Log start
                # We can try to extract job_id from args if it's a common pattern, 
                # but generic logging involves args summary.
                logger.info(f"[{task_name}] Started.")
                
                result = await func(*args, **kwargs)
                
                logger.info(f"[{task_name}] Completed successfully.")
                return result
                
            except Exception as e:
                logger.error(f"[{task_name}] Failed: {str(e)}", exc_info=True)
                # Here we could implement more logic, e.g., updating a global state 
                # if job_id was passed, but knowing *how* to update state depends entirely 
                # on the function signature. 
                # For now, consistent logging is the 'auto-correction' step 1.
                raise e
        return wrapper
    return decorator
