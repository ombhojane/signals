"""
Core Parallel Execution Module - Fan-out/Fan-in pattern for concurrent operations.
"""

import asyncio
import time
from typing import Dict, Any, List, Callable, Coroutine, Optional, TypeVar
from dataclasses import dataclass
from core.logging import logger

T = TypeVar('T')


@dataclass
class TaskResult:
    """Result of a parallel task."""
    name: str
    success: bool
    data: Any
    error: Optional[str] = None
    duration_ms: float = 0


async def gather_with_results(
    tasks: Dict[str, Coroutine],
    timeout: Optional[float] = 30.0
) -> Dict[str, TaskResult]:
    """
    Execute multiple coroutines in parallel and collect results.
    
    Unlike asyncio.gather, this:
    - Never fails completely if one task fails
    - Returns structured results with timing and error info
    - Logs progress to terminal
    
    Args:
        tasks: Dict of {name: coroutine}
        timeout: Optional timeout for all tasks
        
    Returns:
        Dict of {name: TaskResult}
    """
    num_tasks = len(tasks)
    logger.parallel_start("data_fetch", num_tasks)
    start_time = time.time()
    
    results = {}
    
    async def wrapped_task(name: str, coro: Coroutine) -> TaskResult:
        """Wrap a coroutine to capture result and timing."""
        task_start = time.time()
        try:
            data = await coro
            duration = (time.time() - task_start) * 1000
            return TaskResult(
                name=name,
                success=True,
                data=data,
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - task_start) * 1000
            logger.error(f"Task {name} failed: {str(e)}")
            return TaskResult(
                name=name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=duration
            )
    
    # Create wrapped tasks
    wrapped = {name: wrapped_task(name, coro) for name, coro in tasks.items()}
    
    # Execute all in parallel
    if timeout:
        try:
            gathered = await asyncio.wait_for(
                asyncio.gather(*wrapped.values(), return_exceptions=False),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Parallel execution timed out after {timeout}s")
            # Return partial results
            for name in tasks:
                if name not in results:
                    results[name] = TaskResult(
                        name=name,
                        success=False,
                        data=None,
                        error="Timeout"
                    )
            return results
    else:
        gathered = await asyncio.gather(*wrapped.values(), return_exceptions=False)
    
    # Collect results
    for result in gathered:
        results[result.name] = result
    
    # Log summary
    total_duration = (time.time() - start_time) * 1000
    success_count = sum(1 for r in results.values() if r.success)
    failed_count = num_tasks - success_count
    
    logger.parallel_done("data_fetch", total_duration, success_count, failed_count)
    
    return results


async def run_parallel_agents(
    agent_calls: Dict[str, Coroutine],
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Run multiple AI agent calls in parallel.
    
    Args:
        agent_calls: Dict of {agent_name: agent_coroutine}
        timeout: Timeout for all agents
        
    Returns:
        Dict of {agent_name: result} - failed agents return error dict
    """
    logger.parallel_start("ai_agents", len(agent_calls))
    start_time = time.time()
    
    results = await gather_with_results(agent_calls, timeout=timeout)
    
    # Convert to simple dict format expected by callers
    output = {}
    for name, result in results.items():
        if result.success:
            output[name] = result.data
        else:
            output[name] = {
                "status": "error",
                "error": result.error,
                "agent_type": name
            }
    
    total_duration = (time.time() - start_time) * 1000
    success_count = sum(1 for r in results.values() if r.success)
    failed_count = len(results) - success_count
    
    logger.parallel_done("ai_agents", total_duration, success_count, failed_count)
    
    return output


def make_async(sync_func: Callable) -> Callable:
    """
    Convert a sync function to async by running in thread pool.
    Use for sync HTTP calls that would otherwise block.
    """
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: sync_func(*args, **kwargs))
    return async_wrapper
