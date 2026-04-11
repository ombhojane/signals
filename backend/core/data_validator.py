"""
Data Validator - Pre-flight checks for data quality before AI analysis.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from core.logging import logger


@dataclass
class DataValidationResult:
    """Result of data validation."""
    is_valid: bool
    source: str
    reason: Optional[str] = None
    

def validate_dex_data(data: Optional[Dict[str, Any]]) -> DataValidationResult:
    """
    Validate DEX data before sending to AI.
    
    Returns:
        DataValidationResult with validation status
    """
    if not data:
        return DataValidationResult(
            is_valid=False,
            source="dex",
            reason="No DEX data received"
        )
    
    # Check for pairs data
    pairs = data.get("pairs")
    if not pairs or not isinstance(pairs, list) or len(pairs) == 0:
        return DataValidationResult(
            is_valid=False,
            source="dex",
            reason="No trading pairs found"
        )
    
    # Check first pair has essential fields
    pair = pairs[0]
    required_fields = ["priceUsd", "liquidity"]
    missing = [f for f in required_fields if not pair.get(f)]
    
    if missing:
        return DataValidationResult(
            is_valid=False,
            source="dex",
            reason=f"Missing required fields: {missing}"
        )
    
    return DataValidationResult(is_valid=True, source="dex")


def validate_gmgn_data(data: Optional[Dict[str, Any]]) -> DataValidationResult:
    """
    Validate GMGN data before sending to AI.
    
    Returns:
        DataValidationResult with validation status
    """
    if not data:
        return DataValidationResult(
            is_valid=False,
            source="gmgn",
            reason="No GMGN data received"
        )
    
    # Check for analysis data
    analysis = data.get("analysis") or data
    token_stats = analysis.get("token_stats")
    
    # If token_stats is null, GMGN lookup failed
    if token_stats is None:
        chain = analysis.get("chain", "unknown")
        return DataValidationResult(
            is_valid=False,
            source="gmgn",
            reason=f"GMGN returned no token stats (chain: {chain})"
        )
    
    return DataValidationResult(is_valid=True, source="gmgn")


def validate_safety_data(data: Optional[Dict[str, Any]]) -> DataValidationResult:
    """
    Validate safety/rug check data before sending to AI.

    Returns:
        DataValidationResult with validation status
    """
    if not data:
        return DataValidationResult(
            is_valid=False,
            source="safety",
            reason="No safety data received"
        )

    # Check for meaningful data (not just defaults)
    risk_score = data.get("overall_risk_score")
    risk_level = data.get("risk_level", "UNKNOWN")

    if risk_level == "UNKNOWN" and risk_score is None:
        return DataValidationResult(
            is_valid=False,
            source="safety",
            reason="Safety APIs returned no usable data"
        )

    return DataValidationResult(is_valid=True, source="safety")


def validate_twitter_data(data: Optional[Dict[str, Any]]) -> DataValidationResult:
    """
    Validate Twitter data before sending to AI.
    
    Returns:
        DataValidationResult with validation status
    """
    if not data:
        return DataValidationResult(
            is_valid=False,
            source="twitter",
            reason="No Twitter data received"
        )
    
    # Check for error status
    if data.get("status") == "error":
        error = data.get("error", "Unknown error")
        return DataValidationResult(
            is_valid=False,
            source="twitter",
            reason=f"Twitter API error: {error}"
        )
    
    # Check for tweets
    tweets = data.get("tweets", [])
    if not tweets or len(tweets) == 0:
        return DataValidationResult(
            is_valid=False,
            source="twitter",
            reason="No tweets found"
        )
    
    return DataValidationResult(is_valid=True, source="twitter")


def validate_all_data(
    dex_data: Optional[Dict[str, Any]],
    gmgn_data: Optional[Dict[str, Any]],
    twitter_data: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, DataValidationResult], bool, List[str]]:
    """
    Validate all data sources before AI analysis.
    
    Returns:
        Tuple of (validation_results, can_proceed, warnings)
    """
    results = {
        "dex": validate_dex_data(dex_data),
        "gmgn": validate_gmgn_data(gmgn_data),
        "twitter": validate_twitter_data(twitter_data)
    }
    
    warnings = []
    for source, result in results.items():
        if not result.is_valid:
            msg = f"{source.upper()}: {result.reason}"
            warnings.append(msg)
            logger.warning(msg)
    
    # Can proceed if at least DEX data is valid
    can_proceed = results["dex"].is_valid
    
    if not can_proceed:
        logger.error("Cannot proceed: No valid DEX data")
    
    return results, can_proceed, warnings


def get_analysis_context(validations: Dict[str, DataValidationResult]) -> str:
    """
    Generate context string for AI about data availability.
    
    This helps the AI understand what data is available/missing.
    """
    available = []
    missing = []
    
    for source, result in validations.items():
        if result.is_valid:
            available.append(source.upper())
        else:
            missing.append(f"{source.upper()} ({result.reason})")
    
    context = f"Available data sources: {', '.join(available) if available else 'None'}"
    if missing:
        context += f"\nUnavailable: {', '.join(missing)}"
    
    return context
