"""
Dev helper: makes a Sepolia USDC self-transfer so the x402 middleware has a
valid on-chain payment proof to verify. Uses AGENT_PRIVATE_KEY from .env.

Usage:
  ./venv/Scripts/python scripts/dev_sepolia_pay.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

# Load .env from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

RPC = os.getenv("BASE_RPC_URL", "https://sepolia.base.org")
USDC = Web3.to_checksum_address("0x036CbD53842c5426634e7929541eC2318f3dCF7e")
AMOUNT_WEI = 10_000  # 0.01 USDC

ERC20_ABI = [
    {
        "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def main() -> None:
    key = os.getenv("AGENT_PRIVATE_KEY")
    if not key:
        raise SystemExit("AGENT_PRIVATE_KEY not found in .env")

    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        raise SystemExit(f"cannot reach RPC {RPC}")

    account = w3.eth.account.from_key(key)
    me = account.address

    usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    bal = usdc.functions.balanceOf(me).call()
    if bal < AMOUNT_WEI:
        raise SystemExit(f"wallet USDC balance {bal / 1e6} < {AMOUNT_WEI / 1e6}")

    tx = usdc.functions.transfer(me, AMOUNT_WEI).build_transaction(
        {
            "from": me,
            "nonce": w3.eth.get_transaction_count(me),
            "gas": 80_000,
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
            "chainId": w3.eth.chain_id,
        }
    )
    signed = w3.eth.account.sign_transaction(tx, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"broadcast: 0x{tx_hash.hex().removeprefix('0x')}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    ok = receipt["status"] == 1
    print(f"status:    {'ok' if ok else 'failed'}  block={receipt['blockNumber']}  gas={receipt['gasUsed']}")

    if ok:
        h = "0x" + tx_hash.hex().removeprefix("0x")
        print()
        print("Use in x402 request:")
        print(f"  curl -H 'X-Payment: {h}' http://127.0.0.1:8001/signal/base/0x4200000000000000000000000000000000000006")


if __name__ == "__main__":
    main()
