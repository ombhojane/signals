"""
X402 Middleware - HTTP 402 paywall enforced via on-chain USDC transfer.

Spec (minimal subset of the x402 protocol):
  1. Client requests a protected path without payment.
  2. Server returns HTTP 402 with X-Payment-* headers describing the required
     transfer (recipient, asset, amount, network, chain id).
  3. Client sends a USDC transferFrom → recipient on the target chain.
  4. Client retries the request with header `X-Payment: <tx_hash>`.
  5. Server verifies: status success, correct recipient/asset/amount, unused.
  6. Server returns 200 with the response.
"""

import os
from dataclasses import dataclass
from typing import Iterable

from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from web3 import Web3

load_dotenv()


ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


@dataclass
class X402Config:
    enabled: bool
    rpc_url: str
    recipient: str
    asset_address: str
    amount_wei: int
    chain_id: int
    network_name: str
    protected_prefixes: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "X402Config":
        enabled = os.getenv("X402_ENABLED", "false").lower() == "true"
        prefixes = tuple(
            p.strip() for p in os.getenv("X402_PROTECTED_PATHS", "/signal").split(",") if p.strip()
        )
        return cls(
            enabled=enabled,
            rpc_url=os.getenv("BASE_RPC_URL", "http://127.0.0.1:8545"),
            recipient=os.getenv("X402_RECIPIENT", ""),
            asset_address=os.getenv(
                "X402_ASSET_ADDRESS", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
            ),
            amount_wei=int(os.getenv("X402_AMOUNT_WEI", "10000")),  # 0.01 USDC
            chain_id=int(os.getenv("X402_CHAIN_ID", "8453")),
            network_name=os.getenv("X402_NETWORK", "base"),
            protected_prefixes=prefixes,
        )


class X402Middleware(BaseHTTPMiddleware):
    def __init__(self, app, config: X402Config):
        super().__init__(app)
        self.config = config
        self._used_tx_hashes: set[str] = set()

        if config.enabled:
            if not config.recipient:
                raise ValueError("X402_RECIPIENT must be set when X402_ENABLED=true")
            self.recipient = Web3.to_checksum_address(config.recipient)
            self.asset = Web3.to_checksum_address(config.asset_address)
            self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"x402: cannot reach RPC {config.rpc_url}")

    def _is_protected(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.config.protected_prefixes)

    def _payment_challenge(self) -> JSONResponse:
        headers = {
            "X-Payment-Recipient": self.recipient,
            "X-Payment-Asset": self.asset,
            "X-Payment-Amount": str(self.config.amount_wei),
            "X-Payment-Network": self.config.network_name,
            "X-Payment-Chain-Id": str(self.config.chain_id),
        }
        body = {
            "error": "payment_required",
            "accepts": [
                {
                    "scheme": "onchain_transfer",
                    "network": self.config.network_name,
                    "chain_id": self.config.chain_id,
                    "asset": self.asset,
                    "recipient": self.recipient,
                    "amount": str(self.config.amount_wei),
                    "amount_human": f"{self.config.amount_wei / 10**6:.6f} USDC",
                }
            ],
            "instructions": (
                "Send the required USDC amount on the specified chain to the recipient, "
                "then retry with header `X-Payment: <tx_hash>`."
            ),
        }
        return JSONResponse(status_code=402, headers=headers, content=body)

    def _verify_payment(self, tx_hash: str) -> tuple[bool, str]:
        tx_hash = tx_hash.lower()
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        if tx_hash in self._used_tx_hashes:
            return False, "tx already used"

        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            return False, f"tx not found: {e}"

        if receipt["status"] != 1:
            return False, "tx reverted"

        asset_lower = self.asset.lower()
        recipient_lower = self.recipient.lower()

        for log in receipt["logs"]:
            if log["address"].lower() != asset_lower:
                continue
            if len(log["topics"]) < 3:
                continue
            topic0 = log["topics"][0].hex()
            if not topic0.startswith("0x"):
                topic0 = "0x" + topic0
            if topic0.lower() != ERC20_TRANSFER_TOPIC:
                continue
            to_topic = log["topics"][2].hex()
            if not to_topic.startswith("0x"):
                to_topic = "0x" + to_topic
            to_addr = "0x" + to_topic[-40:]
            if to_addr.lower() != recipient_lower:
                continue

            data = log["data"]
            data_hex = data.hex() if hasattr(data, "hex") else str(data)
            if not data_hex.startswith("0x"):
                data_hex = "0x" + data_hex
            value = int(data_hex, 16)

            if value < self.config.amount_wei:
                return False, f"insufficient amount: {value} < {self.config.amount_wei}"

            self._used_tx_hashes.add(tx_hash)
            return True, "ok"

        return False, "no matching USDC transfer to recipient"

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.config.enabled or not self._is_protected(request.url.path):
            return await call_next(request)

        payment_header = request.headers.get("X-Payment")
        if not payment_header:
            return self._payment_challenge()

        tx_hash = payment_header.removeprefix("tx:").strip()
        ok, reason = self._verify_payment(tx_hash)
        if not ok:
            return JSONResponse(
                status_code=402,
                content={"error": "payment_invalid", "detail": reason},
            )

        response = await call_next(request)
        response.headers["X-Payment-Verified"] = tx_hash
        return response
