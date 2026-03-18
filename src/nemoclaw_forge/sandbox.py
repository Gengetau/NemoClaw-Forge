import asyncio
import logging
import time
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

class Sandbox:
    """Secure simulation layer for executing tasks safely."""
    
    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds
        
    async def run_sandboxed(self, task_func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> Any:
        """Execute a task with bounded time and mock resource monitoring."""
        start_time = time.time()
        logger.info("Sandbox execution started.")
        
        try:
            # Enforce execution time limit
            result = await asyncio.wait_for(task_func(*args, **kwargs), timeout=self.timeout_seconds)
            
            elapsed = time.time() - start_time
            logger.info(f"Sandbox execution completed safely in {elapsed:.2f}s.")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Sandbox security violation: Task exceeded {self.timeout_seconds}s limit.")
            raise
        except Exception as e:
            logger.error(f"Sandbox caught an exception during execution: {e}")
            raise
