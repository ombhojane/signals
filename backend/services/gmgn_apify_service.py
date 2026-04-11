import os
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

class TokenStatData(BaseModel):
    """Model for token statistics data from GMGN"""
    token_address: str
    chain: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    holders: Optional[int] = None
    transactions: Optional[int] = None
    price_change_24h: Optional[float] = None
    created_at: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class TrenchesData(BaseModel):
    """Model for trenches/new tokens data from GMGN"""
    tokens: List[Dict[str, Any]]
    total_count: int
    chain: str
    data_type: str
    raw_data: Optional[Dict[str, Any]] = None

class GMGNApifyService:
    """Service for fetching GMGN data using Apify scrapers"""
    
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN environment variable is required")
        
        self.client = ApifyClient(self.api_token)
        
        # Actor IDs from the documentation
        self.token_stat_actor_id = "scHeYjt83t536kluo"  # GMGN Token Stat Scraper
        self.trenches_actor_id = "q1bD7XdljP0Rvb3qc"    # GMGN Trenches Scraper
    
    async def get_token_stats(self, token_addresses: List[str], chain: str = "sol") -> List[TokenStatData]:
        """
        Fetch token statistics using GMGN Token Stat Scraper
        
        Args:
            token_addresses: List of token addresses to analyze
            chain: Blockchain chain (default: "sol")
            
        Returns:
            List of TokenStatData objects
        """
        from core.constants import get_chain_id
        
        try:
            # Use centralized chain mapping
            mapped_chain = get_chain_id(chain, "gmgn")
            print(f"[GMGN Token Stats] Original chain: {chain}, Mapped chain: {mapped_chain}")
            
            # Prepare the Actor input
            run_input = {
                "tokenAddresses": token_addresses,
                "chain": mapped_chain,
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": [],
                },
            }

            
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.token_stat_actor_id).call(run_input=run_input)
            
            # Debug: Print run info
            print(f"Actor run completed. Run ID: {run.get('id')}, Dataset ID: {run.get('defaultDatasetId')}")
            
            # Fetch results from the dataset
            results = []
            dataset_client = self.client.dataset(run["defaultDatasetId"])
            
            # Get all items from dataset
            items = list(dataset_client.iterate_items())
            print(f"Found {len(items)} items in dataset")
            
            for item in items:
                print(f"Processing item: {item}")  # Debug print
                
                # Extract data with better field mapping
                token_data = TokenStatData(
                    token_address=item.get("tokenAddress", item.get("address", "")),
                    chain=chain,
                    name=item.get("name", item.get("tokenName")),
                    symbol=item.get("symbol", item.get("tokenSymbol")),
                    price=self._safe_float(item.get("price", item.get("currentPrice"))),
                    market_cap=self._safe_float(item.get("marketCap", item.get("marketCapUsd"))),
                    volume_24h=self._safe_float(item.get("volume24h", item.get("volume24H"))),
                    liquidity=self._safe_float(item.get("liquidity", item.get("liquidityUsd"))),
                    holders=self._safe_int(item.get("holders", item.get("holderCount"))),
                    transactions=self._safe_int(item.get("transactions", item.get("txCount"))),
                    price_change_24h=self._safe_float(item.get("priceChange24h", item.get("priceChange24H"))),
                    created_at=item.get("createdAt", item.get("createdTime")),
                    raw_data=item
                )
                results.append(token_data)
            
            return results
            
        except Exception as e:
            print(f"Error fetching token stats: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_trenches_data(self, chain: str = "sol", data_type: str = "new_creation", limit: int = 80) -> TrenchesData:
        """
        Get trenches data from GMGN using Apify Trenches Scraper
        
        Args:
            chain: Blockchain network (sol, bsc) - NOTE: only sol/bsc supported
            data_type: Type of data to fetch (new_creation, trending, etc.)
            limit: Number of tokens to fetch
        """
        from core.constants import get_chain_id, LAUNCHPAD_PLATFORMS, BSC_PLATFORMS
        
        # Trenches API only supports sol and bsc
        SUPPORTED_TRENCHES_CHAINS = {"sol", "bsc"}
        mapped_chain = get_chain_id(chain, "gmgn")
        
        if mapped_chain not in SUPPORTED_TRENCHES_CHAINS:
            print(f"Trenches API does not support chain: {chain} (mapped: {mapped_chain}). Skipping.")
            return TrenchesData(
                tokens=[],
                total_count=0,
                chain=chain,
                data_type=data_type,
                raw_data={"skipped": True, "reason": f"Chain '{mapped_chain}' not supported by Trenches API"}
            )
        
        try:
            print(f"Original chain: {chain}, Mapped chain: {mapped_chain}")
            
            # Prepare the Actor input using centralized platform lists
            run_input = {
                "chain": mapped_chain,
                "dataType": data_type,
                "limit": limit,
                "launchpadPlatforms": LAUNCHPAD_PLATFORMS,
                "bscPlatforms": BSC_PLATFORMS,
                "metricFilters": [],
                "socialFilters": [],
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": [],
                },
            }
            
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.trenches_actor_id).call(run_input=run_input)
            
            # Debug: Print run info
            print(f"Trenches Actor run completed. Run ID: {run.get('id')}, Dataset ID: {run.get('defaultDatasetId')}")
            
            # Fetch results from the dataset
            dataset_client = self.client.dataset(run["defaultDatasetId"])
            tokens = list(dataset_client.iterate_items())
            
            print(f"Found {len(tokens)} tokens in trenches dataset")
            
            # Debug: Print first few tokens
            for i, token in enumerate(tokens[:3]):
                print(f"Token {i+1}: {token}")
            
            return TrenchesData(
                tokens=tokens,
                total_count=len(tokens),
                chain=chain,
                data_type=data_type,
                raw_data={"run_id": run.get("id"), "dataset_id": run["defaultDatasetId"]}
            )
            
        except Exception as e:
            print(f"Error fetching trenches data: {str(e)}")
            import traceback
            traceback.print_exc()
            return TrenchesData(
                tokens=[],
                total_count=0,
                chain=chain,
                data_type=data_type,
                raw_data={"error": str(e)}
            )
    
    async def get_token_analysis(self, token_address: str, chain: str = "sol") -> Dict[str, Any]:
        """
        Get comprehensive token analysis combining both scrapers
        
        Args:
            token_address: Token address to analyze
            chain: Blockchain chain
            
        Returns:
            Dictionary containing combined analysis data
        """
        try:
            # Get token stats
            token_stats = await self.get_token_stats([token_address], chain)
            token_stat = token_stats[0] if token_stats else None
            
            # Get trenches data for context (recent tokens)
            trenches_data = await self.get_trenches_data(chain=chain, limit=20)
            
            # Find if this token appears in recent trenches
            token_in_trenches = None
            for token in trenches_data.tokens:
                if token.get("tokenAddress") == token_address:
                    token_in_trenches = token
                    break
            
            return {
                "token_address": token_address,
                "chain": chain,
                "token_stats": token_stat.dict() if token_stat else None,
                "in_recent_trenches": token_in_trenches is not None,
                "trenches_data": token_in_trenches,
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "token_address": token_address,
                "chain": chain,
                "error": str(e),
                "status": "error"
            }
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

# Global service instance
gmgn_service = GMGNApifyService()

# Convenience functions for backward compatibility
async def get_gmgn_token_stats(token_addresses: List[str], chain: str = "sol") -> List[TokenStatData]:
    """Get token statistics for given addresses"""
    return await gmgn_service.get_token_stats(token_addresses, chain)

async def get_gmgn_trenches(chain: str = "sol", limit: int = 80) -> TrenchesData:
    """Get trenches/new tokens data"""
    return await gmgn_service.get_trenches_data(chain=chain, limit=limit)

async def get_gmgn_analysis(token_address: str, chain: str = "sol") -> Dict[str, Any]:
    """Get comprehensive token analysis"""
    return await gmgn_service.get_token_analysis(token_address, chain)
