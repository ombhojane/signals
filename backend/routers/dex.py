"""
DEX Analytics Router - Endpoints for DEX data and token prices.
"""

from fastapi import APIRouter, HTTPException
from services.dex_api import get_dex_data
from services.moralisapi import fetch_token_price
from models.schemas import DexAnalyticsResponse


router = APIRouter(prefix="", tags=["DEX Analytics"])


@router.get("/token-price")
def get_token_price(token_address: str):
    """Get token price from Moralis API."""
    price_data = fetch_token_price(token_address)
    if "error" in price_data:
        raise HTTPException(status_code=400, detail=price_data["error"])
    return price_data


@router.get("/dex-analytics", response_model=DexAnalyticsResponse)
async def get_dex_analytics(chainId: str, pairAddress: str):
    """
    Get DEX analytics data using DexScreener API.
    
    Args:
        chainId: The blockchain chain ID (e.g., 'ethereum', 'bsc', 'solana')
        pairAddress: The pair address/ID
    """
    try:
        # Fetch real data from DexScreener API
        dex_data = get_dex_data(chainId, pairAddress)
        
        # Extract pair data
        if dex_data and 'pairs' in dex_data and dex_data['pairs']:
            pair_info = dex_data['pairs'][0]
        else:
            pair_info = {}
        
        # Extract key metrics
        volume_24h = float(pair_info.get('volume', {}).get('h24', 0))
        liquidity_usd = float(pair_info.get('liquidity', {}).get('usd', 0))
        price_change_24h = float(pair_info.get('priceChange', {}).get('h24', 0))
        
        # Extract token info
        base_token = pair_info.get('baseToken', {})
        quote_token = pair_info.get('quoteToken', {})
        pair_name = f"{base_token.get('symbol', 'TOKEN')}/{quote_token.get('symbol', 'USD')}"
        
        # Get DEX info
        dex_id = pair_info.get('dexId', 'Unknown DEX')
        
        # Transform to expected response format
        return {
            "total_dex_volume": volume_24h,
            "dex_volume_change": price_change_24h,
            "total_liquidity": liquidity_usd,
            "liquidity_change": price_change_24h,
            "unique_traders": int(pair_info.get('txns', {}).get('h24', {}).get('buys', 0)) + int(pair_info.get('txns', {}).get('h24', {}).get('sells', 0)),
            "traders_change": price_change_24h,
            "liquidity_pool": [
                {
                    "platform": dex_id.title(),
                    "pair": pair_name,
                    "liquidity": liquidity_usd / 1000000 if liquidity_usd else 0,
                    "change": price_change_24h,
                }
            ],
            "whale_transactions": [
                {
                    "address": pair_info.get('pairAddress', 'N/A')[:10] + "...",
                    "amount": volume_24h / 1000000 if volume_24h else 0,
                    "asset": base_token.get('symbol', 'TOKEN'),
                    "time_ago": "Live data",
                }
            ],
        }
        
    except Exception as e:
        # Fallback to default data if API fails
        return {
            "total_dex_volume": 0,
            "dex_volume_change": 0,
            "total_liquidity": 0,
            "liquidity_change": 0,
            "unique_traders": 0,
            "traders_change": 0,
            "liquidity_pool": [
                {
                    "platform": "DexScreener",
                    "pair": f"Chain: {chainId}",
                    "liquidity": 0,
                    "change": 0,
                }
            ],
            "whale_transactions": [
                {
                    "address": pairAddress[:10] + "..." if pairAddress else "N/A",
                    "amount": 0,
                    "asset": "TOKEN",
                    "time_ago": f"Error: {str(e)}",
                }
            ],
        }
