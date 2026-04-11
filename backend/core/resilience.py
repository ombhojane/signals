"""
Core Resilience Module - Circuit breaker and retry patterns for external API calls.
No external dependencies - uses only Python stdlib.
"""

import time
import asyncio
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from core.logging import logger


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Simple in-memory circuit breaker.
    
    - CLOSED: Normal operation, counting failures
    - OPEN: After threshold failures, reject immediately
    - HALF_OPEN: After timeout, allow one request to test
    """
    name: str
    failure_threshold: int = 3
    recovery_timeout: float = 30.0  # seconds
    
    # State
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    
    def record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.circuit_close(self.name)
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.circuit_open(self.name)
    
    def can_execute(self) -> bool:
        """Check if we can make a call."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        
        # HALF_OPEN: allow one test request
        return True
    
    def get_state_info(self) -> dict:
        """Get current state info for debugging."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold
        }


# Global circuit breakers for each service
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name)
    return _circuit_breakers[name]


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retry with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Multiplier for each retry
        retryable_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            service_name = func.__name__
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                        logger.retry(service_name, attempt, max_attempts, delay)
                        await asyncio.sleep(delay)
                    else:
                        raise
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            service_name = func.__name__
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                        logger.retry(service_name, attempt, max_attempts, delay)
                        time.sleep(delay)
                    else:
                        raise
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def with_circuit_breaker(service_name: str, fallback_value: Any = None):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        service_name: Name of the service (for tracking)
        fallback_value: Value to return when circuit is open
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cb = get_circuit_breaker(service_name)
            
            if not cb.can_execute():
                logger.warning(f"Circuit open for {service_name}, returning fallback")
                return fallback_value
            
            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cb = get_circuit_breaker(service_name)
            
            if not cb.can_execute():
                logger.warning(f"Circuit open for {service_name}, returning fallback")
                return fallback_value
            
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def resilient(
    service_name: str,
    max_retries: int = 3,
    fallback_value: Any = None
):
    """
    Combined decorator for resilience: circuit breaker + retry.
    
    Args:
        service_name: Name of the service
        max_retries: Max retry attempts
        fallback_value: Value when circuit is open
    """
    def decorator(func: Callable) -> Callable:
        # Apply both decorators
        wrapped = with_retry(max_attempts=max_retries)(func)
        wrapped = with_circuit_breaker(service_name, fallback_value)(wrapped)
        return wrapped
    return decorator


async def run_with_timeout(coro, timeout: float, default: Any = None):
    """Run a coroutine with timeout, returning default on timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        return default


def get_all_circuit_states() -> dict:
    """Get state of all circuit breakers for monitoring."""
    return {name: cb.get_state_info() for name, cb in _circuit_breakers.items()}
