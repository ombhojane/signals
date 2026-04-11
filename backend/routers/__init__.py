"""
API Routers
"""

from routers.dex import router as dex_router
from routers.gmgn import router as gmgn_router
from routers.ai_analysis import router as ai_analysis_router
from routers.chat import router as chat_router
from routers.vault import router as vault_router
from routers.signal import router as signal_router

__all__ = [
    "dex_router",
    "gmgn_router",
    "ai_analysis_router",
    "chat_router",
    "vault_router",
    "signal_router",
]
