"""
Signals Backend - FastAPI Application Entry Point

A clean, modular backend for cryptocurrency token analysis.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.config import settings
from routers import (
    dex_router,
    gmgn_router,
    ai_analysis_router,
    chat_router,
    vault_router,
    signal_router,
    token_scan_router,
    wallet_router,
)
from services.x402_middleware import X402Config, X402Middleware


# Create FastAPI application
app = FastAPI(
    title="Signals API",
    description="Cryptocurrency token analysis and AI-powered insights",
    version="2.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Payment-Recipient",
        "X-Payment-Asset",
        "X-Payment-Amount",
        "X-Payment-Network",
        "X-Payment-Chain-Id",
        "X-Payment-Verified",
    ],
)

# x402 paywall — enabled only when X402_ENABLED=true in env
_x402_config = X402Config.from_env()
print(
    f"[x402] enabled={_x402_config.enabled} "
    f"recipient={_x402_config.recipient} "
    f"protected={_x402_config.protected_prefixes} "
    f"amount_wei={_x402_config.amount_wei}"
)
if _x402_config.enabled:
    app.add_middleware(X402Middleware, config=_x402_config)

# Include routers
app.include_router(dex_router)
app.include_router(gmgn_router)
app.include_router(ai_analysis_router)
app.include_router(chat_router)
app.include_router(vault_router)
app.include_router(signal_router)
app.include_router(token_scan_router)
app.include_router(wallet_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Signals API",
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    missing_config = settings.validate()
    return {
        "status": "healthy" if not missing_config else "degraded",
        "missing_config": missing_config,
    }


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
