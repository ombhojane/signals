"""
GMGN Router - Endpoints for token data and trending tokens.
Now powered by DexScreener + GeckoTerminal (free APIs) instead of Apify.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from services.token_data_service import (
    get_token_stats,
    get_trending_tokens,
    get_token_analysis,
    token_data_service,
)
from services.token_safety_service import get_safety_report
from models.schemas import TokenStatsRequest, TrenchesRequest


router = APIRouter(prefix="/gmgn", tags=["GMGN"])


@router.post("/token-stats")
async def get_token_stats_endpoint(request: TokenStatsRequest):
    """
    Get token statistics using DexScreener + GeckoTerminal.

    Args:
        request: TokenStatsRequest containing token addresses and chain

    Returns:
        List of token statistics data
    """
    try:
        results = await get_token_stats(request.token_addresses, request.chain)
        return {
            "status": "success",
            "data": [result.model_dump() for result in results],
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token stats: {str(e)}")


@router.post("/trenches")
async def get_trenches_endpoint(request: TrenchesRequest):
    """
    Get trending/new tokens data from DexScreener.

    Args:
        request: TrenchesRequest containing search parameters

    Returns:
        Trending tokens data
    """
    try:
        result = await get_trending_tokens(
            chain=request.chain,
            limit=request.limit
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trenches data: {str(e)}")


@router.get("/token-analysis/{token_address}")
async def get_token_analysis_endpoint(token_address: str, chain: str = "sol"):
    """
    Get comprehensive token analysis combining price data + safety checks.

    Args:
        token_address: Token address to analyze
        chain: Blockchain chain (default: sol)

    Returns:
        Comprehensive token analysis data
    """
    try:
        # Fetch token data and safety report in parallel
        import asyncio
        token_task = get_token_analysis(token_address, chain)
        safety_task = get_safety_report(token_address, chain)

        token_result, safety_result = await asyncio.gather(
            token_task, safety_task, return_exceptions=True
        )

        # Handle partial failures
        token_data = token_result if not isinstance(token_result, Exception) else {"error": str(token_result)}
        safety_data = safety_result.to_dict() if not isinstance(safety_result, Exception) and hasattr(safety_result, 'to_dict') else {}

        return {
            **token_data,
            "safety_report": safety_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing token: {str(e)}")


@router.get("/trending")
async def get_trending_tokens_endpoint(chain: str = "sol", limit: int = 20):
    """
    Get trending tokens from DexScreener.

    Args:
        chain: Blockchain chain (default: sol)
        limit: Number of tokens to fetch (default: 20)

    Returns:
        List of trending tokens
    """
    try:
        result = await get_trending_tokens(chain=chain, limit=limit)
        return {
            "status": "success",
            "chain": chain,
            "trending_tokens": result.get("tokens", []),
            "count": result.get("total_count", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending tokens: {str(e)}")
