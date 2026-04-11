"""
Vault Router - Endpoints for AI-driven vault trades and reasoning retrieval.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import reasoning_store
from services.vault_service import get_vault_service


router = APIRouter(tags=["Vault"])


class ExecuteTradeRequest(BaseModel):
    token_in: str
    token_out: str
    amount_in: int = Field(..., description="Raw amount (with decimals) of token_in")
    amount_out_min: int = 0
    pool_fee: int = 500
    reasoning: str = Field(..., min_length=1)
    confidence: int = Field(..., ge=0, le=100)


class ExecuteTradeResponse(BaseModel):
    tx_hash: str
    reasoning_hash: str
    amount_out: int
    block_number: int


@router.post("/vault/execute", response_model=ExecuteTradeResponse)
def execute_vault_trade(req: ExecuteTradeRequest):
    """
    Run a trade through the vault. Reasoning is stored off-chain, its keccak256
    hash and confidence are logged on-chain via TradeExecuted.
    """
    service = get_vault_service()

    reasoning_hash = reasoning_store.store(
        text=req.reasoning,
        confidence=req.confidence,
        token_in=req.token_in,
        token_out=req.token_out,
    )

    try:
        result = service.execute_trade(
            token_in=req.token_in,
            token_out=req.token_out,
            pool_fee=req.pool_fee,
            amount_in=req.amount_in,
            amount_out_minimum=req.amount_out_min,
            reasoning_text=req.reasoning,
            confidence=req.confidence,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"executeTrade failed: {e}")

    reasoning_store.update_tx_hash(reasoning_hash, result.tx_hash)

    return ExecuteTradeResponse(
        tx_hash=result.tx_hash,
        reasoning_hash=reasoning_hash,
        amount_out=result.amount_out,
        block_number=result.block_number,
    )


@router.get("/reasoning/{reasoning_hash}")
def get_reasoning(reasoning_hash: str):
    row = reasoning_store.get(reasoning_hash)
    if not row:
        raise HTTPException(status_code=404, detail="reasoning not found")
    return row


@router.get("/vault/state")
def get_vault_state():
    service = get_vault_service()
    return {
        "address": service.vault_address,
        "asset": service.asset_address(),
        "total_assets": service.total_assets(),
        "total_supply": service.total_supply(),
        "position_open": service.position_open(),
    }
