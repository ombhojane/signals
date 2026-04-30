"""
Vault Service - web3.py wrapper around the SignalsVault contract.

Executes AI-driven trades on Uniswap V3 through the deployed vault, passing the
reasoning hash and confidence score so every trade is verifiably linked to the
LLM decision that produced it.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from web3 import Web3
from web3.types import TxReceipt

load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ABI_PATH = _REPO_ROOT / "contracts" / "out" / "SignalsVault.sol" / "SignalsVault.json"


def _load_abi() -> list:
    with open(_ABI_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["abi"]


@dataclass
class TradeResult:
    tx_hash: str
    amount_out: int
    reasoning_hash: str
    block_number: int


class VaultService:
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        vault_address: Optional[str] = None,
        agent_private_key: Optional[str] = None,
    ):
        self.rpc_url = rpc_url or os.getenv("BASE_RPC_URL", "http://127.0.0.1:8545")
        self.vault_address = vault_address or os.getenv("VAULT_ADDRESS")
        self.agent_private_key = agent_private_key or os.getenv("AGENT_PRIVATE_KEY")

        if not self.vault_address:
            raise ValueError("VAULT_ADDRESS is not set")
        if not self.agent_private_key:
            raise ValueError("AGENT_PRIVATE_KEY is not set")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC {self.rpc_url}")

        self.account = self.w3.eth.account.from_key(self.agent_private_key)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.vault_address),
            abi=_load_abi(),
        )

    # ─── Read helpers ─────────────────────────────────────────────

    def total_assets(self) -> int:
        return self.contract.functions.totalAssets().call()

    def total_supply(self) -> int:
        return self.contract.functions.totalSupply().call()

    def position_open(self) -> bool:
        return self.contract.functions.positionOpen().call()

    def asset_address(self) -> str:
        return self.contract.functions.asset().call()

    # ─── Write: executeTrade ──────────────────────────────────────

    def execute_trade(
        self,
        token_in: str,
        token_out: str,
        pool_fee: int,
        amount_in: int,
        amount_out_minimum: int,
        reasoning_text: str,
        confidence: int,
    ) -> TradeResult:
        """
        Submit an executeTrade transaction signed by the agent key.

        Args:
            token_in: ERC-20 address to swap from
            token_out: ERC-20 address to swap to
            pool_fee: Uniswap V3 pool fee in hundredths of a bip (500, 3000, 10000)
            amount_in: Raw amount of token_in (no decimal adjustment here)
            amount_out_minimum: Slippage floor
            reasoning_text: Full LLM rationale — hashed on-chain, stored off-chain
            confidence: 0-100

        Returns:
            TradeResult with tx hash, amount out, and the reasoning hash committed.
        """
        if not 0 <= confidence <= 100:
            raise ValueError("confidence must be in [0, 100]")

        reasoning_hash_bytes = Web3.keccak(text=reasoning_text)
        _h = reasoning_hash_bytes.hex()
        reasoning_hash_hex = _h if _h.startswith("0x") else "0x" + _h

        fn = self.contract.functions.executeTrade(
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            pool_fee,
            amount_in,
            amount_out_minimum,
            reasoning_hash_bytes,
            confidence,
        )

        tx = fn.build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 600_000,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": self.w3.eth.chain_id,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, private_key=self.agent_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt: TxReceipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise RuntimeError(f"executeTrade reverted, tx={tx_hash.hex()}")

        amount_out = self._parse_amount_out(receipt)

        return TradeResult(
            tx_hash=tx_hash.hex(),
            amount_out=amount_out,
            reasoning_hash=reasoning_hash_hex,
            block_number=receipt["blockNumber"],
        )

    def _parse_amount_out(self, receipt: TxReceipt) -> int:
        """Decode amountOut from the TradeExecuted event."""
        logs = self.contract.events.TradeExecuted().process_receipt(receipt)
        if not logs:
            return 0
        return int(logs[0]["args"]["amountOut"])


_service: Optional[VaultService] = None


def get_vault_service() -> VaultService:
    """Lazy singleton so importing the module doesn't require env vars to be set."""
    global _service
    if _service is None:
        _service = VaultService()
    return _service
