"""
Twitter API v2 Service using twitterapi.io
Provides real-time tweet fetching for cryptocurrency tokens
"""

import os
import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TweetAuthor(BaseModel):
    """Twitter user/author model"""
    userName: str
    name: str
    id: str
    isBlueVerified: Optional[bool] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    description: Optional[str] = None


class TweetData(BaseModel):
    """Tweet data model"""
    id: str
    text: str
    url: Optional[str] = None
    createdAt: str
    likeCount: int = 0
    retweetCount: int = 0
    replyCount: int = 0
    viewCount: int = 0
    author: Optional[TweetAuthor] = None
    lang: Optional[str] = None


class TwitterAPIResponse(BaseModel):
    """Twitter API response model"""
    tweets: List[TweetData]
    has_next_page: bool = False
    next_cursor: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None


class TwitterAPIService:
    """Service for interacting with twitterapi.io"""
    
    BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Twitter API service with API key"""
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        if not self.api_key:
            logger.warning("Twitter API key not found. Set TWITTER_API_KEY environment variable.")
    
    def search_tweets(
        self,
        query: str,
        query_type: str = "Latest",
        cursor: str = "",
        max_tweets: int = 20
    ) -> TwitterAPIResponse:
        """
        Search tweets using advanced search API
        
        Args:
            query: Search query (e.g., "#bitcoin OR $BTC")
            query_type: "Latest" or "Top"
            cursor: Pagination cursor
            max_tweets: Maximum number of tweets to fetch
            
        Returns:
            TwitterAPIResponse with tweets and pagination info
        """
        if not self.api_key:
            return TwitterAPIResponse(
                tweets=[],
                status="error",
                error="Twitter API key not configured"
            )
        
        try:
            headers = {
                "X-API-Key": self.api_key
            }
            
            params = {
                "query": query,
                "queryType": query_type,
                "cursor": cursor
            }
            
            logger.info(f"Searching tweets with query: {query}")
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse tweets
            tweets = []
            for tweet_raw in data.get("tweets", [])[:max_tweets]:
                try:
                    # Parse author
                    author_data = tweet_raw.get("author", {})
                    author = TweetAuthor(
                        userName=author_data.get("userName", "unknown"),
                        name=author_data.get("name", "Unknown"),
                        id=author_data.get("id", ""),
                        isBlueVerified=author_data.get("isBlueVerified", False),
                        followers=author_data.get("followers", 0),
                        following=author_data.get("following", 0),
                        description=author_data.get("description", "")
                    ) if author_data else None
                    
                    # Parse tweet
                    tweet = TweetData(
                        id=tweet_raw.get("id", ""),
                        text=tweet_raw.get("text", ""),
                        url=tweet_raw.get("url", ""),
                        createdAt=tweet_raw.get("createdAt", ""),
                        likeCount=tweet_raw.get("likeCount", 0),
                        retweetCount=tweet_raw.get("retweetCount", 0),
                        replyCount=tweet_raw.get("replyCount", 0),
                        viewCount=tweet_raw.get("viewCount", 0),
                        author=author,
                        lang=tweet_raw.get("lang", "")
                    )
                    tweets.append(tweet)
                    
                except Exception as e:
                    logger.error(f"Error parsing tweet: {e}")
                    continue
            
            return TwitterAPIResponse(
                tweets=tweets,
                has_next_page=data.get("has_next_page", False),
                next_cursor=data.get("next_cursor", ""),
                status="success"
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Twitter API request failed: {e}")
            return TwitterAPIResponse(
                tweets=[],
                status="error",
                error=f"API request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Twitter API: {e}")
            return TwitterAPIResponse(
                tweets=[],
                status="error",
                error=f"Unexpected error: {str(e)}"
            )


def build_crypto_search_query(
    token_symbol: Optional[str] = None,
    token_name: Optional[str] = None,
    token_address: Optional[str] = None,
    additional_keywords: List[str] = None
) -> str:
    """
    Build a Twitter search query for cryptocurrency tokens
    
    Args:
        token_symbol: Token symbol (e.g., "BTC", "SOL")
        token_name: Token name (e.g., "Bitcoin", "Solana")
        token_address: Token contract address
        additional_keywords: Additional keywords to include
        
    Returns:
        Formatted Twitter search query
    """
    query_parts = []
    
    if token_symbol:
        # Search for both $SYMBOL and #SYMBOL
        query_parts.append(f'("${token_symbol}" OR "#{token_symbol}")')
    
    if token_name:
        query_parts.append(f'"{token_name}"')
    
    if token_address:
        # Shorten address for better results (first 8 and last 6 chars)
        if len(token_address) > 20:
            short_addr = f"{token_address[:8]}...{token_address[-6:]}"
            query_parts.append(f'"{short_addr}"')
    
    if additional_keywords:
        keywords_query = " OR ".join([f'"{kw}"' for kw in additional_keywords])
        query_parts.append(f"({keywords_query})")
    
    # Join all parts with OR
    query = " OR ".join(query_parts) if query_parts else "cryptocurrency"
    
    return query


async def fetch_token_tweets(
    token_symbol: Optional[str] = None,
    token_name: Optional[str] = None,
    token_address: Optional[str] = None,
    max_tweets: int = 20,
    query_type: str = "Latest",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch tweets related to a cryptocurrency token.
    Results are cached for 5 minutes to reduce API costs.

    Args:
        token_symbol: Token symbol (e.g., "BTC")
        token_name: Token name (e.g., "Bitcoin")
        token_address: Token contract address
        max_tweets: Maximum number of tweets to fetch
        query_type: "Latest" or "Top"
        api_key: Twitter API key (optional, can use env variable)

    Returns:
        Dictionary with tweets and metadata
    """
    from core.cache import twitter_cache

    # Check cache first
    cache_key = f"tweets:{token_symbol}:{token_name}:{token_address}"
    cached = twitter_cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for tweets: {token_symbol or token_name}")
        return cached

    service = TwitterAPIService(api_key)

    # Build search query
    query = build_crypto_search_query(
        token_symbol=token_symbol,
        token_name=token_name,
        token_address=token_address
    )

    logger.info(f"Fetching tweets for token: {token_symbol or token_name}")
    logger.info(f"Search query: {query}")

    # Fetch tweets
    response = service.search_tweets(
        query=query,
        query_type=query_type,
        max_tweets=max_tweets
    )

    # Convert to dict for easier handling
    result = {
        "query": query,
        "query_type": query_type,
        "total_tweets": len(response.tweets),
        "status": response.status,
        "error": response.error,
        "tweets": [tweet.dict() for tweet in response.tweets]
    }

    # Cache successful results
    if response.status == "success" and response.tweets:
        twitter_cache.set(cache_key, result)

    return result
