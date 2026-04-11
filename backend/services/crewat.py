"""
Token Analysis Agents - AI agents for cryptocurrency analysis with structured outputs.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from core.logging import logger
from core.output_parser import parse_llm_response, extract_json_from_response
from models.agent_responses import (
    MarketAnalysisResponse,
    GMGNAnalysisResponse,
    SocialAnalysisResponse,
    PredictionResponse
)

load_dotenv()

# Initialize Google AI models - API key from environment variable
google_api_key = os.getenv("GOOGLE_API_KEY")

# Different models for different agents
llm_analyzer = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.3,
    google_api_key=google_api_key
)

llm_gmgn = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.2,
    google_api_key=google_api_key
)

llm_social = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.4,
    google_api_key=google_api_key
)

llm_predictor = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.1,
    google_api_key=google_api_key
)

JSON_INSTRUCTION = """

CRITICAL: Return ONLY a valid JSON object. Do NOT wrap it in markdown code fences.
Do NOT include any text before or after the JSON such as ``` or ```json"""


class TokenAnalysisAgents:
    """LangChain-based token analysis agents using Google AI models with structured outputs."""
    
    def __init__(self):
        self.llm_analyzer = llm_analyzer
        self.llm_gmgn = llm_gmgn
        self.llm_social = llm_social
        self.llm_predictor = llm_predictor
    
    def _parse_response(
        self, 
        response_text: str, 
        model_class, 
        agent_type: str
    ) -> Dict[str, Any]:
        """Parse LLM response and return structured output."""
        validated, raw_dict, error = parse_llm_response(response_text, model_class)
        
        if validated:
            return {
                "agent_type": agent_type,
                "analysis": validated.model_dump(),
                "status": "success",
                "parsed": True
            }
        elif raw_dict:
            return {
                "agent_type": agent_type,
                "analysis": raw_dict,
                "status": "success",
                "parsed": True,
                "validation_warning": error
            }
        else:
            # Fallback: return raw text
            logger.warning(f"Could not parse {agent_type} response as JSON")
            return {
                "agent_type": agent_type,
                "analysis": response_text,
                "status": "success",
                "parsed": False,
                "parse_error": error
            }
    
    async def market_signals(self, dex_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DEX/market data and provide structured insights."""
        logger.info("Running market signals analysis...")
        
        try:
            prompt = f"""As a cryptocurrency data analyst expert, analyze the following DEX/market data.

DEX Data: {json.dumps(dex_data, indent=2)}

Analyze:
1. Volume trends and significance
2. Liquidity analysis and market depth
3. Trading activity patterns
4. Price impact assessment
5. Market health indicators
6. Risk factors identified

Return a JSON object with these exact fields:
- summary: string (brief overview)
- volume_analysis: string (volume insights)
- liquidity_analysis: string (liquidity insights)
- trading_patterns: string (trading activity)
- risk_assessment: string (risk factors)
- market_health: integer 1-10 (market health score)
- recommendations: array of strings (key takeaways)
{JSON_INSTRUCTION}"""
            
            response = await self.llm_analyzer.ainvoke([HumanMessage(content=prompt)])
            return self._parse_response(response.content, MarketAnalysisResponse, "dex_analyzer")
            
        except Exception as e:
            logger.error(f"Market signals error: {str(e)}")
            return {
                "agent_type": "dex_analyzer",
                "analysis": None,
                "status": "error",
                "error": str(e)
            }
    
    async def gmgn_signals(self, gmgn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GMGN token data for rug detection with structured outputs."""
        logger.info("Running GMGN safety analysis...")
        
        try:
            prompt = f"""As a GMGN analysis expert specializing in rug detection and token safety, analyze this data.

GMGN Data: {json.dumps(gmgn_data, indent=2)}

Focus on:
1. Rug pull risk assessment
2. Token holder distribution analysis
3. Creator/developer behavior patterns
4. Liquidity lock status
5. Trading pattern anomalies
6. Overall safety score

Return a JSON object with these exact fields:
- rug_risk_score: integer 0-100 (0=safe, 100=scam)
- safety_factors: array of strings (positive indicators)
- risk_factors: array of strings (concerning factors)
- holder_analysis: string (holder distribution insights)
- recommendation: string, one of "SAFE", "CAUTION", "AVOID"
- summary: string (brief safety assessment)
{JSON_INSTRUCTION}"""
            
            response = await self.llm_gmgn.ainvoke([HumanMessage(content=prompt)])
            return self._parse_response(response.content, GMGNAnalysisResponse, "gmgn_analyzer")
            
        except Exception as e:
            logger.error(f"GMGN signals error: {str(e)}")
            return {
                "agent_type": "gmgn_analyzer",
                "analysis": None,
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_social_data(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze social sentiment (alias for analyze_social_sentiment)."""
        return await self.analyze_social_sentiment(social_data)
    
    async def analyze_social_sentiment(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze social sentiment with structured outputs."""
        logger.info("Running social sentiment analysis...")
        
        try:
            prompt = f"""As a social sentiment analysis expert, analyze this social media data.

Social Data: {json.dumps(social_data, indent=2)}

Analyze:
1. Overall sentiment score and trend
2. Community engagement levels
3. Influencer involvement and impact
4. Trending keywords and implications
5. Hype vs genuine interest indicators
6. Potential manipulation signs

Return a JSON object with these exact fields:
- sentiment_score: integer 0-100 (0=bearish, 100=bullish)
- engagement_level: string (community engagement assessment)
- influencer_impact: string (influencer analysis)
- hype_assessment: string (genuine vs artificial hype)
- trend_analysis: string (trending patterns)
- community_health: integer 0-100 (community strength)
- summary: string (social sentiment overview)
{JSON_INSTRUCTION}"""
            
            response = await self.llm_social.ainvoke([HumanMessage(content=prompt)])
            return self._parse_response(response.content, SocialAnalysisResponse, "social_analyzer")
            
        except Exception as e:
            logger.error(f"Social analysis error: {str(e)}")
            return {
                "agent_type": "social_analyzer",
                "analysis": None,
                "status": "error",
                "error": str(e)
            }
    
    async def predict_token_movement(self, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict token movement with structured outputs."""
        logger.info("Running prediction model...")
        
        try:
            prompt = f"""As a cryptocurrency prediction expert, analyze all data and make a prediction.

Combined Analysis Data: {json.dumps(combined_data, indent=2)}

Based on DEX data, GMGN analysis, and social sentiment, provide:
1. Short-term prediction (24-48 hours)
2. Medium-term outlook (1-7 days)
3. Key factors influencing the prediction
4. Confidence level
5. Action signal recommendation
6. Risk-reward assessment

Return a JSON object with these exact fields:
- action_signal: string, one of "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
- confidence_level: integer 0-100
- short_term_prediction: string (24-48h outlook)
- medium_term_prediction: string (1-7 days outlook)
- key_factors: array of strings (main prediction factors)
- risk_level: string, one of "LOW", "MEDIUM", "HIGH"
- summary: string (prediction summary and rationale)
{JSON_INSTRUCTION}"""
            
            response = await self.llm_predictor.ainvoke([HumanMessage(content=prompt)])
            return self._parse_response(response.content, PredictionResponse, "predictor")
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                "agent_type": "predictor",
                "analysis": None,
                "status": "error",
                "error": str(e)
            }


# Initialize the agents
token_agents = TokenAnalysisAgents()
