"""
Wallet Management Router
Handles wallet connection, detection, and user account management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

wallet_router = APIRouter(prefix="/api/wallet", tags=["wallet"])

# Supported wallet types
SUPPORTED_WALLETS = {
    "phantom": {
        "name": "Phantom",
        "icon": "🎭",
        "chains": ["solana", "ethereum", "polygon"],
        "installed": True,
    },
    "metamask": {
        "name": "MetaMask",
        "icon": "🦊",
        "chains": ["ethereum", "polygon", "arbitrum", "optimism"],
        "installed": True,
    },
    "solflare": {
        "name": "Solflare",
        "icon": "🔦",
        "chains": ["solana"],
        "installed": True,
    },
    "backpack": {
        "name": "Backpack",
        "icon": "🎒",
        "chains": ["solana"],
        "installed": True,
    },
    "ledger": {
        "name": "Ledger Live",
        "icon": "📱",
        "chains": ["ethereum", "solana", "polygon"],
        "installed": True,
    },
    "walletconnect": {
        "name": "WalletConnect",
        "icon": "🔗",
        "chains": ["ethereum", "polygon", "arbitrum", "optimism", "solana"],
        "installed": True,
    },
}


class WalletInfo(BaseModel):
    """Wallet information response"""
    id: str
    name: str
    icon: str
    chains: list[str]
    installed: bool


class ConnectWalletRequest(BaseModel):
    """Request to connect a wallet"""
    wallet_id: str
    chain: str = "solana"


class ConnectWalletResponse(BaseModel):
    """Response after wallet connection"""
    success: bool
    wallet_id: str
    address: str | None = None
    chain: str
    message: str


class WalletSession(BaseModel):
    """User wallet session"""
    address: str
    wallet_id: str
    chain: str
    connected: bool
    timestamp: int


@wallet_router.get("/available", response_model=list[WalletInfo])
async def get_available_wallets():
    """
    Get list of available wallets that user can connect to.
    Returns all supported wallets with their capabilities.
    """
    return [
        WalletInfo(
            id=wallet_id,
            name=wallet_data["name"],
            icon=wallet_data["icon"],
            chains=wallet_data["chains"],
            installed=wallet_data["installed"],
        )
        for wallet_id, wallet_data in SUPPORTED_WALLETS.items()
    ]


@wallet_router.get("/available/{chain}", response_model=list[WalletInfo])
async def get_wallets_for_chain(chain: str):
    """
    Get list of wallets available for a specific chain.
    
    Supported chains: solana, ethereum, polygon, arbitrum, optimism
    """
    chain = chain.lower()
    if chain not in ["solana", "ethereum", "polygon", "arbitrum", "optimism"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported chain. Use: solana, ethereum, polygon, arbitrum, optimism"
        )
    
    return [
        WalletInfo(
            id=wallet_id,
            name=wallet_data["name"],
            icon=wallet_data["icon"],
            chains=wallet_data["chains"],
            installed=wallet_data["installed"],
        )
        for wallet_id, wallet_data in SUPPORTED_WALLETS.items()
        if chain in wallet_data["chains"]
    ]


@wallet_router.post("/connect", response_model=ConnectWalletResponse)
async def connect_wallet(request: ConnectWalletRequest):
    """
    Connect a user's wallet.
    This endpoint simulates wallet connection for demo purposes.
    In production, this would interact with actual wallet providers.
    """
    wallet_id = request.wallet_id.lower()
    chain = request.chain.lower()
    
    # Validate wallet exists
    if wallet_id not in SUPPORTED_WALLETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown wallet: {wallet_id}. Available: {list(SUPPORTED_WALLETS.keys())}"
        )
    
    wallet_data = SUPPORTED_WALLETS[wallet_id]
    
    # Validate chain is supported by wallet
    if chain not in wallet_data["chains"]:
        raise HTTPException(
            status_code=400,
            detail=f"Wallet {wallet_data['name']} does not support chain '{chain}'. Supported: {wallet_data['chains']}"
        )
    
    # Generate mock address for demo (in production, this would come from wallet provider)
    if chain == "solana":
        mock_address = "9B5X6r5c9K8v3Q9P7L2M5n8d1q4s7w0x3z6c9V"
    elif chain == "ethereum":
        mock_address = "0x742d35Cc6634C0532925a3b844Bc5e8f1BD52B4A"
    else:
        mock_address = "0x742d35Cc6634C0532925a3b844Bc5e8f1BD52B4A"
    
    return ConnectWalletResponse(
        success=True,
        wallet_id=wallet_id,
        address=mock_address,
        chain=chain,
        message=f"Successfully connected {wallet_data['name']} on {chain}"
    )


@wallet_router.post("/disconnect")
async def disconnect_wallet():
    """Disconnect the current wallet session."""
    return {
        "success": True,
        "message": "Wallet disconnected successfully"
    }


@wallet_router.get("/session")
async def get_wallet_session():
    """Get current wallet session (if any)."""
    # This would normally check session/JWT token
    return {
        "connected": False,
        "address": None,
        "wallet_id": None,
        "chain": None
    }
