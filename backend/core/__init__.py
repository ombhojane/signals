"""
Signals Core Module
"""

from core.config import settings, Settings
from core.constants import (
    CHAIN_MAPPINGS,
    LAUNCHPAD_PLATFORMS,
    BSC_PLATFORMS,
    get_chain_id,
    DEFAULT_MAX_TWEETS,
    DEFAULT_TRENCHES_LIMIT,
    DEFAULT_CHAIN,
)
from core.exceptions import (
    SignalsError,
    ExternalAPIError,
    ConfigurationError,
    TokenNotFoundError,
    AnalysisError,
)
from core.logging import logger, log_execution
from core.resilience import (
    with_retry,
    with_circuit_breaker,
    resilient,
    get_all_circuit_states,
)
from core.parallel import (
    gather_with_results,
    run_parallel_agents,
    make_async,
    TaskResult,
)

__all__ = [
    # Config
    "settings",
    "Settings",
    # Constants
    "CHAIN_MAPPINGS",
    "LAUNCHPAD_PLATFORMS", 
    "BSC_PLATFORMS",
    "get_chain_id",
    "DEFAULT_MAX_TWEETS",
    "DEFAULT_TRENCHES_LIMIT",
    "DEFAULT_CHAIN",
    # Exceptions
    "SignalsError",
    "ExternalAPIError",
    "ConfigurationError",
    "TokenNotFoundError",
    "AnalysisError",
    # Logging
    "logger",
    "log_execution",
    # Resilience
    "with_retry",
    "with_circuit_breaker",
    "resilient",
    "get_all_circuit_states",
    # Parallel
    "gather_with_results",
    "run_parallel_agents",
    "make_async",
    "TaskResult",
]

