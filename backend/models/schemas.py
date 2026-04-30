"""
Pydantic Models/Schemas for API request and response validation.
"""

from pydantic import BaseModel
from typing import List, Optional


# --- DEX Analytics Models ---

class LiquidityPool(BaseModel):
    platform: str
    pair: str
    liquidity: float
    change: float


class WhaleTransaction(BaseModel):
    address: str
    amount: float
    asset: str
    time_ago: str


class DexAnalyticsResponse(BaseModel):
    total_dex_volume: float
    dex_volume_change: float
    total_liquidity: float
    liquidity_change: float
    unique_traders: int
    traders_change: float
    liquidity_pool: List[LiquidityPool]
    whale_transactions: List[WhaleTransaction]


# --- AI HypeScan Models ---

class FeatureEngineering(BaseModel):
    name: str
    weight: int
    color: str
    value: int


class BlockchainRecognition(BaseModel):
    name: str
    timeFrame: str
    riskColor: str
    riskLevel: str
    riskPercentage: int


class AlertThreshold(BaseModel):
    name: str
    status: str
    color: str
    bgColor: str


class AIHypeScanResponse(BaseModel):
    strength: str
    confidence: int
    pattern: str
    patternPhase: str
    prediction: str
    forecast: str
    featureEngineering: List[FeatureEngineering]
    blockchainRecognition: List[BlockchainRecognition]
    alertThresholds: List[AlertThreshold]


# --- Risk Assessment Models ---

class RiskAssessmentResponse(BaseModel):
    sectionId: str
    overallRiskScore: str
    riskLevel: str
    smartContractSafetyPercentage: int
    smartContractStatus: str
    liquidityLockStatus: str
    liquidityLockRemainingDays: int
    ownershipStatus: str
    ownershipStatusDescription: str
    mintFunctionStatus: str
    mintFunctionDescription: str
    transferRestrictions: str
    transferRestrictionsDescription: str
    liquidityRisk: str
    liquidityRiskPercentage: int
    concentrationRisk: str
    concentrationRiskPercentage: int
    smartContractRisk: str
    smartContractRiskPercentage: int


# --- Historical Data Models ---

class HistoricalResponse(BaseModel):
    roi: int
    pumpPatterns: int
    averagePumpReturn: int
    recoveryTime: int
    activeAlerts: int
    highPriority: int
    triggeredToday: int
    triggeredChange: int
    successRate: int
    responseTime: float


# --- Chat Models ---

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: float = 1.0
    max_tokens: int = 1024


# --- GMGN Request Models ---

class TokenStatsRequest(BaseModel):
    token_addresses: List[str]
    chain: str = "sol"


class TrenchesRequest(BaseModel):
    chain: str = "sol"
    data_type: str = "new_creation"
    limit: int = 80
    launchpad_platforms: Optional[List[str]] = None
