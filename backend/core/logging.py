"""
Core Logging Module - Structured terminal logging with colors.
"""

import sys
import time
from datetime import datetime
from typing import Any, Optional
from functools import wraps
import asyncio


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Foreground colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


class Logger:
    """Structured terminal logger with colors and timing."""
    
    def __init__(self, name: str = "Signals"):
        self.name = name
        self._start_times = {}
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def _log(self, level: str, color: str, message: str, **kwargs):
        """Internal log method."""
        timestamp = self._timestamp()
        prefix = f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {color}{level}{Colors.RESET}"

        # Format extra kwargs
        extra = ""
        if kwargs:
            extra_parts = [f"{k}={v}" for k, v in kwargs.items()]
            extra = f" {Colors.GRAY}| {' | '.join(extra_parts)}{Colors.RESET}"

        line = f"{prefix} {message}{extra}"
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", errors="replace").decode("ascii"))
        sys.stdout.flush()
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO ", Colors.BLUE, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message."""
        self._log(" OK  ", Colors.GREEN, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARN ", Colors.YELLOW, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log("ERROR", Colors.RED, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", Colors.GRAY, message, **kwargs)
    
    def api_call(self, service: str, endpoint: str = ""):
        """Log API call start."""
        self._log("> API", Colors.CYAN, f"{service}", endpoint=endpoint)
    
    def api_success(self, service: str, duration_ms: float):
        """Log API call success."""
        self._log("< API", Colors.GREEN, f"{service}", duration=f"{duration_ms:.0f}ms")
    
    def api_error(self, service: str, error: str, duration_ms: float = 0):
        """Log API call error."""
        self._log("x API", Colors.RED, f"{service}: {error}", duration=f"{duration_ms:.0f}ms")
    
    def retry(self, service: str, attempt: int, max_attempts: int, wait_sec: float):
        """Log retry attempt."""
        self._log("RETRY", Colors.YELLOW, f"{service}", attempt=f"{attempt}/{max_attempts}", wait=f"{wait_sec:.1f}s")
    
    def circuit_open(self, service: str):
        """Log circuit breaker opened."""
        self._log("! CB ", Colors.RED, f"Circuit OPEN for {service} - failing fast")
    
    def circuit_close(self, service: str):
        """Log circuit breaker closed."""
        self._log("! CB ", Colors.GREEN, f"Circuit CLOSED for {service} - resuming calls")
    
    def parallel_start(self, task_name: str, num_tasks: int):
        """Log parallel execution start."""
        self._log("| PAR", Colors.MAGENTA, f"Starting {num_tasks} parallel tasks", group=task_name)
    
    def parallel_done(self, task_name: str, duration_ms: float, success: int, failed: int):
        """Log parallel execution complete."""
        status = Colors.GREEN if failed == 0 else Colors.YELLOW
        self._log("| PAR", status, f"Completed {task_name}", 
                  success=success, failed=failed, duration=f"{duration_ms:.0f}ms")
    
    def section(self, title: str):
        """Print a section header."""
        line = "=" * 60
        try:
            print(f"\n{Colors.BOLD}{Colors.CYAN}{line}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.CYAN}  {title.upper()}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.CYAN}{line}{Colors.RESET}\n")
        except UnicodeEncodeError:
            print(f"\n{line}\n  {title.upper()}\n{line}\n")
    
    def start_timer(self, name: str):
        """Start a named timer."""
        self._start_times[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """Stop a named timer and return duration in ms."""
        if name not in self._start_times:
            return 0
        duration = (time.time() - self._start_times[name]) * 1000
        del self._start_times[name]
        return duration


# Global logger instance
logger = Logger()


def log_execution(service_name: str):
    """Decorator to log function execution with timing."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger.api_call(service_name)
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.api_success(service_name, duration)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.api_error(service_name, str(e), duration)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger.api_call(service_name)
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.api_success(service_name, duration)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.api_error(service_name, str(e), duration)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
