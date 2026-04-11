"""
Report Generator - Markdown report generation for token analysis.
"""

import json
from datetime import datetime
from typing import Dict, Any, Union
from utils.formatters import format_number, format_percentage


def _format_analysis(analysis: Union[str, Dict, None]) -> str:
    """
    Format analysis data for markdown output.
    Handles both string (legacy) and dict (structured) formats.
    """
    if analysis is None:
        return "No analysis available"
    
    if isinstance(analysis, str):
        return analysis
    
    if isinstance(analysis, dict):
        # Pretty print the structured output
        return json.dumps(analysis, indent=2, default=str)
    
    # Fallback: convert to string
    return str(analysis)


def generate_markdown_report(
    token_id: str,
    pair_id: str,
    chain_id: str,
    market_data: Dict[str, Any],
    gmgn_data: Dict[str, Any],
    twitter_data: Dict[str, Any],
    ai_data: Dict[str, Any]
) -> str:
    """Generate a comprehensive markdown report for token analysis.
    
    Args:
        token_id: Token address
        pair_id: Pair address
        chain_id: Blockchain chain ID
        market_data: DEX and Moralis data
        gmgn_data: GMGN analysis data
        twitter_data: Twitter social data
        ai_data: AI analysis results
        
    Returns:
        Markdown formatted report string
    """
    lines = []
    
    # Header
    lines.append("#  Token Analysis Report")
    lines.append("")
    lines.append(f"**Token ID:** `{token_id}`")
    lines.append(f"**Pair ID:** `{pair_id}`")
    lines.append(f"**Chain:** {chain_id.upper()}")
    lines.append(f"**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Market Signals Section
    lines.append("## 1. Market Signals Data")
    lines.append("")
    
    if 'dex_data' in market_data and market_data['dex_data'].get('pairs'):
        pair = market_data['dex_data']['pairs'][0]
        lines.append("### DEX Screener Data")
        lines.append("")
        lines.append(f"- **Pair Address:** `{pair.get('pairAddress', 'N/A')}`")
        lines.append(f"- **Base Token:** {pair.get('baseToken', {}).get('symbol', 'N/A')} ({pair.get('baseToken', {}).get('name', 'N/A')})")
        lines.append(f"- **Quote Token:** {pair.get('quoteToken', {}).get('symbol', 'N/A')}")
        lines.append(f"- **Price USD:** {format_number(pair.get('priceUsd'))}")
        lines.append(f"- **Liquidity USD:** {format_number(pair.get('liquidity', {}).get('usd'))}")
        lines.append(f"- **Volume 24h:** {format_number(pair.get('volume', {}).get('h24'))}")
        lines.append(f"- **Price Change 24h:** {format_percentage(pair.get('priceChange', {}).get('h24'))}")
        lines.append(f"- **Market Cap:** {format_number(pair.get('marketCap'))}")
        lines.append("")
    
    # AI Market Analysis
    if 'market_analysis' in ai_data:
        lines.append("### 🤖 AI Market Analysis")
        lines.append("")
        analysis = ai_data['market_analysis'].get('analysis')
        lines.append("```json")
        lines.append(_format_analysis(analysis))
        lines.append("```")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # GMGN Signals Section
    lines.append("## 2. GMGN Signals Data")
    lines.append("")
    
    if 'analysis' in gmgn_data:
        token_stats = gmgn_data['analysis'].get('token_stats')
        if token_stats:
            lines.append("### Token Statistics")
            lines.append("")
            lines.append(f"- **Name:** {token_stats.get('name', 'N/A')}")
            lines.append(f"- **Symbol:** {token_stats.get('symbol', 'N/A')}")
            lines.append(f"- **Price:** {format_number(token_stats.get('price'))}")
            lines.append(f"- **Market Cap:** {format_number(token_stats.get('market_cap'))}")
            lines.append(f"- **Holders:** {token_stats.get('holders', 'N/A')}")
            lines.append("")
    
    # AI GMGN Analysis
    if 'gmgn_analysis' in ai_data:
        lines.append("### 🤖 AI GMGN Safety Analysis")
        lines.append("")
        analysis = ai_data['gmgn_analysis'].get('analysis')
        lines.append("```json")
        lines.append(_format_analysis(analysis))
        lines.append("```")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Twitter Section
    lines.append("## 3. Twitter/Social Signals Data")
    lines.append("")
    
    if twitter_data and twitter_data.get('tweets'):
        lines.append(f"**Search Query:** `{twitter_data.get('query', 'N/A')}`")
        lines.append(f"**Total Tweets:** {twitter_data.get('total_tweets', 0)}")
        lines.append("")
        
        lines.append("### Recent Tweets")
        lines.append("")
        
        for i, tweet in enumerate(twitter_data.get('tweets', [])[:5]):
            author = tweet.get('author', {})
            lines.append(f"#### Tweet {i+1}")
            lines.append("")
            lines.append(f"- **Author:** @{author.get('userName', 'unknown')}")
            lines.append(f"- **Followers:** {author.get('followers', 0):,}")
            lines.append(f"- **Engagement:** {tweet.get('likeCount', 0):,} likes | {tweet.get('retweetCount', 0):,} retweets")
            lines.append("")
    else:
        lines.append("*No Twitter data available*")
        lines.append("")
    
    # AI Social Analysis
    if 'social_analysis' in ai_data:
        lines.append("### 🤖 AI Social Sentiment Analysis")
        lines.append("")
        analysis = ai_data['social_analysis'].get('analysis')
        lines.append("```json")
        lines.append(_format_analysis(analysis))
        lines.append("```")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Final Prediction
    lines.append("## 4. AI Final Prediction")
    lines.append("")
    
    if 'prediction' in ai_data:
        analysis = ai_data['prediction'].get('analysis')
        lines.append("```json")
        lines.append(_format_analysis(analysis))
        lines.append("```")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Data Sources Status
    lines.append("## Data Sources Status")
    lines.append("")
    lines.append(f"- **DEX Data:** {'✓ Available' if 'dex_data' in market_data else '✗ Failed'}")
    lines.append(f"- **GMGN Data:** {'✓ Available' if 'analysis' in gmgn_data else '✗ Failed'}")
    lines.append(f"- **Twitter Data:** {'✓ Available' if twitter_data and twitter_data.get('tweets') else '✗ Failed'}")
    lines.append(f"- **AI Analysis:** {'✓ Complete' if ai_data and 'error' not in ai_data else '✗ Failed'}")
    lines.append("")
    
    lines.append("---")
    lines.append(f"\n*Report generated by  at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(lines)
