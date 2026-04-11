"""
Core Constants - Single source of truth for shared values.
"""

from typing import Dict, List


# Chain ID mappings for different API providers
CHAIN_MAPPINGS: Dict[str, Dict[str, str]] = {
    # DexScreener chain mappings
    "dex": {
        "sol": "solana",
        "solana": "solana",
        "base": "base",
        "eth": "ethereum",
        "ethereum": "ethereum",
        "bsc": "bsc",
    },
    # GMGN / token_data_service chain mappings (short names)
    "gmgn": {
        "solana": "sol",
        "sol": "sol",
        "base": "base",
        "bsc": "bsc",
        "ethereum": "eth",
        "eth": "eth",
    },
    # GeckoTerminal network mappings
    "gecko": {
        "sol": "solana",
        "solana": "solana",
        "eth": "eth",
        "ethereum": "eth",
        "base": "base",
        "bsc": "bsc",
    },
}



def get_chain_id(chain: str, provider: str = "dex") -> str:
    """Get the normalized chain ID for a specific provider.
    
    Args:
        chain: Input chain name (e.g., 'sol', 'solana', 'base')
        provider: API provider ('dex' or 'gmgn')
        
    Returns:
        Normalized chain ID for the provider
    """
    mapping = CHAIN_MAPPINGS.get(provider, {})
    return mapping.get(chain.lower(), chain.lower())


# Supported launchpad platforms for GMGN Trenches scraper
LAUNCHPAD_PLATFORMS: List[str] = [
    "Pump.fun",
    "letsbonk",
    "bags",
    "moonshot_app",
    "heaven",
    "sugar",
    "token_mill",
    "believe",
    "jup_studio",
    "Moonshot",
    "boop",
    "ray_launchpad",
    "meteora_virtual_curve",
    "xstocks",
]

# BSC platforms for GMGN
BSC_PLATFORMS: List[str] = [
    "fourmeme",
    "flap",
]


# Default values
DEFAULT_MAX_TWEETS: int = 20
DEFAULT_TRENCHES_LIMIT: int = 80
DEFAULT_CHAIN: str = "sol"
