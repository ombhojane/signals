"""
Dev helper: deposit test USDC into the Sepolia vault.

Reads AGENT_PRIVATE_KEY and VAULT_ADDRESS from .env at repo root.
Approves USDC then calls vault.deposit(amount, owner).

Usage:
  ./venv/Scripts/python scripts/dev_sepolia_deposit.py --amount 10
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

RPC = os.getenv("BASE_RPC_URL", "https://sepolia.base.org")
USDC = Web3.to_checksum_address("0x036CbD53842c5426634e7929541eC2318f3dCF7e")

ERC20_ABI = [
    {
        "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "approve",
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
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _load_vault_abi() -> list:
    path = REPO_ROOT / "contracts" / "out" / "HypeScanVault.sol" / "HypeScanVault.json"
    return json.loads(path.read_text())["abi"]


def _send_tx(w3: Web3, account, tx: dict) -> dict:
    tx.setdefault("chainId", w3.eth.chain_id)
    tx.setdefault("maxFeePerGas", w3.eth.gas_price * 2)
    tx.setdefault("maxPriorityFeePerGas", w3.to_wei(0.001, "gwei"))
    signed = w3.eth.account.sign_transaction(tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt["status"] != 1:
        raise SystemExit(f"tx reverted: 0x{tx_hash.hex().removeprefix('0x')}")
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", type=float, default=10.0, help="USDC amount (whole units)")
    args = ap.parse_args()

    key = os.getenv("AGENT_PRIVATE_KEY")
    vault_addr = os.getenv("VAULT_ADDRESS")
    if not key:
        raise SystemExit("AGENT_PRIVATE_KEY missing from .env")
    if not vault_addr:
        raise SystemExit("VAULT_ADDRESS missing from .env (paste the Sepolia address in)")

    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        raise SystemExit(f"cannot reach RPC {RPC}")

    account = w3.eth.account.from_key(key)
    me = account.address
    amount_wei = int(args.amount * 10**6)

    usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    vault = w3.eth.contract(address=Web3.to_checksum_address(vault_addr), abi=_load_vault_abi())

    bal = usdc.functions.balanceOf(me).call()
    print(f"USDC balance: {bal / 1e6:.6f}")
    if bal < amount_wei:
        raise SystemExit(f"insufficient USDC: have {bal / 1e6}, need {args.amount}")

    # 1. Approve
    current_allowance = usdc.functions.allowance(me, vault.address).call()
    if current_allowance < amount_wei:
        print(f"[1/2] approve vault for {args.amount} USDC")
        tx = usdc.functions.approve(vault.address, amount_wei).build_transaction(
            {"from": me, "nonce": w3.eth.get_transaction_count(me), "gas": 80_000}
        )
        r = _send_tx(w3, account, tx)
        print(f"      approve tx: 0x{r['transactionHash'].hex().removeprefix('0x')}")
    else:
        print("[1/2] allowance already sufficient")

    # 2. Deposit
    print(f"[2/2] deposit {args.amount} USDC -> shares")
    tx = vault.functions.deposit(amount_wei, me).build_transaction(
        {"from": me, "nonce": w3.eth.get_transaction_count(me), "gas": 250_000}
    )
    r = _send_tx(w3, account, tx)
    print(f"      deposit tx: 0x{r['transactionHash'].hex().removeprefix('0x')}")
    print(f"      block:      {r['blockNumber']}")

    print()
    print("Vault state:")
    print(f"  totalAssets:  {vault.functions.totalAssets().call() / 1e6:.6f} USDC")
    print(f"  totalSupply:  {vault.functions.totalSupply().call() / 1e6:.6f} sVAULT")
    print(f"  your shares:  {vault.functions.balanceOf(me).call() / 1e6:.6f} sVAULT")
    print(f"  positionOpen: {vault.functions.positionOpen().call()}")


if __name__ == "__main__":
    main()
