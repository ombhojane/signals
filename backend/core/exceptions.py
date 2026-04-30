"""
Core Exceptions - Custom exception hierarchy for better error handling.
"""


class SignalsError(Exception):
    """Base exception for all Signals errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ExternalAPIError(SignalsError):
    """Error when external API (DexScreener, GMGN, Twitter, etc.) fails."""
    
    def __init__(self, api_name: str, message: str, status_code: int = None):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(
            f"{api_name} API error: {message}",
            {"api": api_name, "status_code": status_code}
        )


class ConfigurationError(SignalsError):
    """Error when required configuration is missing or invalid."""
    
    def __init__(self, missing_keys: list):
        self.missing_keys = missing_keys
        super().__init__(
            f"Missing required configuration: {', '.join(missing_keys)}",
            {"missing_keys": missing_keys}
        )


class TokenNotFoundError(SignalsError):
    """Error when a token cannot be found."""
    
    def __init__(self, token_address: str, chain: str = None):
        self.token_address = token_address
        self.chain = chain
        super().__init__(
            f"Token not found: {token_address}" + (f" on {chain}" if chain else ""),
            {"token_address": token_address, "chain": chain}
        )


class AnalysisError(SignalsError):
    """Error during AI analysis."""
    
    def __init__(self, agent_type: str, message: str):
        self.agent_type = agent_type
        super().__init__(
            f"Analysis error ({agent_type}): {message}",
            {"agent_type": agent_type}
        )
