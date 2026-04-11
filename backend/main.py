"""
Backend - FastAPI Application Entry Point

A clean, modular backend for cryptocurrency token analysis.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.config import settings
from routers import dex_router, gmgn_router, ai_analysis_router, chat_router


# Create FastAPI application
app = FastAPI(
    title="API",
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
)

# Include routers
app.include_router(dex_router)
app.include_router(gmgn_router)
app.include_router(ai_analysis_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "API",
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
