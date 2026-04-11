"""
Agent Response Models - Pydantic models for structured AI agent outputs.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ActionSignal(str, Enum):
    """Trading action signals."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class RiskLevel(str, Enum):
    """Risk level categories."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Recommendation(str, Enum):
    """Investment recommendations."""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    AVOID = "AVOID"


# =============================================================================
# DEX/Market Analysis Response
# =============================================================================

class MarketAnalysisResponse(BaseModel):
    """Structured response from DEX/market analyzer agent."""
    
    summary: str = Field(description="Brief overview of the analysis")
    volume_analysis: str = Field(description="Volume trends and significance")
    liquidity_analysis: str = Field(description="Liquidity and market depth insights")
    trading_patterns: str = Field(description="Trading activity patterns")
    risk_assessment: str = Field(description="Identified risk factors")
    market_health: int = Field(ge=1, le=10, description="Market health score 1-10")
    recommendations: List[str] = Field(description="Key takeaways and recommendations")


# =============================================================================
# GMGN/Safety Analysis Response
# =============================================================================

class GMGNAnalysisResponse(BaseModel):
    """Structured response from GMGN safety analyzer agent."""
    
    rug_risk_score: int = Field(ge=0, le=100, description="Rug pull risk 0-100")
    safety_factors: List[str] = Field(description="Positive safety indicators")
    risk_factors: List[str] = Field(description="Concerning factors")
    holder_analysis: str = Field(description="Holder distribution insights")
    recommendation: Recommendation = Field(description="SAFE/CAUTION/AVOID")
    summary: str = Field(description="Brief safety assessment")


# =============================================================================
# Social Sentiment Analysis Response
# =============================================================================

class SocialAnalysisResponse(BaseModel):
    """Structured response from social sentiment analyzer agent."""
    
    sentiment_score: int = Field(ge=0, le=100, description="Overall sentiment 0-100")
    engagement_level: str = Field(description="Community engagement assessment")
    influencer_impact: str = Field(description="Influencer analysis")
    hype_assessment: str = Field(description="Genuine vs artificial hype")
    trend_analysis: str = Field(description="Trending patterns")
    community_health: int = Field(ge=0, le=100, description="Community strength 0-100")
    summary: str = Field(description="Social sentiment overview")


# =============================================================================
# Prediction Response
# =============================================================================

class PredictionResponse(BaseModel):
    """Structured response from prediction agent."""
    
    action_signal: ActionSignal = Field(description="Trading signal")
    confidence_level: int = Field(ge=0, le=100, description="Confidence 0-100")
    short_term_prediction: str = Field(description="24-48h outlook")
    medium_term_prediction: str = Field(description="1-7 days outlook")
    key_factors: List[str] = Field(description="Factors driving prediction")
    risk_level: RiskLevel = Field(description="LOW/MEDIUM/HIGH")
    summary: str = Field(description="Prediction rationale")


# =============================================================================
# Data Quality Models
# =============================================================================

class DataQualityStatus(str, Enum):
    """Data availability status."""
    AVAILABLE = "available"
    PARTIAL = "partial"
    MISSING = "missing"
    ERROR = "error"


class DataSourceStatus(BaseModel):
    """Status of a data source."""
    
    source: str
    status: DataQualityStatus
    has_data: bool
    error: Optional[str] = None
    
    @classmethod
    def from_data(cls, source: str, data: Any, error: Optional[str] = None):
        """Create status from raw data."""
        if error:
            return cls(source=source, status=DataQualityStatus.ERROR, has_data=False, error=error)
        
        if data is None:
            return cls(source=source, status=DataQualityStatus.MISSING, has_data=False)
        
        # Check if data is empty dict/list
        if isinstance(data, dict):
            if not data or all(v is None for v in data.values()):
                return cls(source=source, status=DataQualityStatus.MISSING, has_data=False)
            # Check for partial data (some None values)
            if any(v is None for v in data.values()):
                return cls(source=source, status=DataQualityStatus.PARTIAL, has_data=True)
        elif isinstance(data, list):
            if not data:
                return cls(source=source, status=DataQualityStatus.MISSING, has_data=False)
        
        return cls(source=source, status=DataQualityStatus.AVAILABLE, has_data=True)
