"""
DEX API Service - DexScreener integration with resilience patterns.
"""

import requests
import time
from typing import Dict, Any
from core.logging import logger
from core.resilience import with_retry, with_circuit_breaker


@with_circuit_breaker("dexscreener", fallback_value={})
@with_retry(max_attempts=3, base_delay=1.0)
def get_dex_data(chain_id: str, pair_id: str) -> dict:
    """
    Get DEX pair data from DexScreener API with retry and circuit breaker.
    
    Args:
        chain_id: The blockchain chain ID (e.g., 'ethereum', 'bsc', 'solana')
        pair_id: The pair address/ID
        
    Returns:
        dict: JSON response from the API
    """
    start = time.time()
    logger.api_call("DexScreener", endpoint=f"{chain_id}/{pair_id[:16]}...")
    
    try:
        # First try to get by pair address
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_id}",
            headers={"Accept": "*/*"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # DexScreener returns {'pair': {...}} for single pair
        # Convert to {'pairs': [...]} format for consistency
        if 'pair' in data and data['pair']:
            result = {'pairs': [data['pair']]}
            duration = (time.time() - start) * 1000
            logger.api_success("DexScreener", duration)
            return result
        
        if 'pairs' in data and data['pairs']:
            duration = (time.time() - start) * 1000
            logger.api_success("DexScreener", duration)
            return data
            
    except requests.exceptions.RequestException:
        # If pair lookup fails, try searching by token address
        pass
    
    # Fallback: search by token address
    try:
        logger.debug("DexScreener pair lookup failed, trying search...")
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/search?q={pair_id}",
            headers={"Accept": "*/*"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        duration = (time.time() - start) * 1000
        logger.api_success("DexScreener (search)", duration)
        return result
        
    except Exception as e:
        duration = (time.time() - start) * 1000
        logger.api_error("DexScreener", str(e), duration)
        raise