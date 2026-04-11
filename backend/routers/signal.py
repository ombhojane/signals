"""
Signal Router - Pay-per-inference AI signal API (protected by x402 middleware).

Returns an AI decision + reasoning hash for a given token. Callers pay $0.01
USDC per call, verified via on-chain transfer to the agent's receiver wallet.
"""

from fastapi import APIRouter, HTTPException

from services import reasoning_store
from services.crewat import token_agents
from services.token_data_service import get_token_analysis
from services.token_safety_service import get_safety_report


router = APIRouter(tags=["Signal"])


@router.get("/signal/{chain}/{token_address}")
async def get_signal(chain: str, token_address: str):
    """
    Return an AI-generated trading signal for `token_address` on `chain`.

    Pipeline:
      1. Fetch token data (DexScreener + GeckoTerminal) and safety (GoPlus/RugCheck)
      2. Run the LLM prediction agent over the combined data
      3. Store the reasoning text, return the keccak256 hash + decision fields
    """
    try:
        token_data = await get_token_analysis(token_address, chain)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"token data fetch failed: {e}")

    try:
        safety = await get_safety_report(token_address, chain)
        safety_dict = safety.to_dict() if hasattr(safety, "to_dict") else {}
    except Exception:
        safety_dict = {}

    combined = {
        "market_data": token_data,
        "safety_data": safety_dict,
    }

    try:
        prediction = await token_agents.predict_token_movement(combined)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ai prediction failed: {e}")

    analysis = prediction.get("analysis")
    if not isinstance(analysis, dict):
        raise HTTPException(status_code=502, detail="ai returned unparseable output")

    action = analysis.get("action_signal", "HOLD")
    confidence = int(analysis.get("confidence_level", 0) or 0)
    summary = analysis.get("summary") or "No summary available"
    short_term = analysis.get("short_term_prediction") or ""
    reasoning_text = (
        f"Action: {action}\n"
        f"Confidence: {confidence}\n"
        f"Short-term: {short_term}\n"
        f"Summary: {summary}\n"
    )

    reasoning_hash = reasoning_store.store(
        text=reasoning_text,
        confidence=confidence,
        token_in=None,
        token_out=token_address,
    )

    return {
        "chain": chain,
        "token_address": token_address,
        "action": action,
        "confidence": confidence,
        "reasoning_hash": reasoning_hash,
        "reasoning_url": f"/reasoning/{reasoning_hash}",
        "key_factors": analysis.get("key_factors", []),
        "risk_level": analysis.get("risk_level", "UNKNOWN"),
    }
