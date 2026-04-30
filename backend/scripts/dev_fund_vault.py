"""
Dev helper: funds a local Anvil-forked vault with test USDC and deposits it.

Usage (from backend/):
  ./venv/Scripts/python scripts/dev_fund_vault.py \
    --vault 0x210312E3772bF2136bcE150B2182ccEd695CE62B \
    --amount 1000
"""

import argparse
import json
from pathlib import Path

from web3 import Web3

# Base mainnet (and fork) constants
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
# Uniswap V3 WETH/USDC 0.05% pool — holds millions in USDC, perfect to impersonate
USDC_WHALE = Web3.to_checksum_address("0xd0b53D9277642d899DF5C87A3966A349A798F224")

# Anvil default account #2 — becomes our test depositor
DEPOSITOR = Web3.to_checksum_address("0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC")
DEPOSITOR_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]


def load_vault_abi() -> list:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "contracts"
        / "out"
        / "HypeScanVault.sol"
        / "HypeScanVault.json"
    )
    return json.loads(path.read_text())["abi"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default="http://127.0.0.1:8545")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--amount", type=int, default=1000, help="USDC amount (whole units)")
    args = ap.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc))
    assert w3.is_connected(), f"RPC not reachable: {args.rpc}"

    amount_wei = args.amount * 10**6  # USDC has 6 decimals
    vault_addr = Web3.to_checksum_address(args.vault)

    print(f"[1/5] Fund depositor with ETH for gas")
    w3.provider.make_request("anvil_setBalance", [DEPOSITOR, hex(10**18)])
    w3.provider.make_request("anvil_setBalance", [USDC_WHALE, hex(10**18)])

    print(f"[2/5] Impersonate USDC whale {USDC_WHALE[:10]}...")
    w3.provider.make_request("anvil_impersonateAccount", [USDC_WHALE])

    usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    tx_hash = usdc.functions.transfer(DEPOSITOR, amount_wei).transact({"from": USDC_WHALE})
    w3.eth.wait_for_transaction_receipt(tx_hash)

    w3.provider.make_request("anvil_stopImpersonatingAccount", [USDC_WHALE])
    bal = usdc.functions.balanceOf(DEPOSITOR).call()
    print(f"       depositor USDC balance: {bal / 1e6:,.2f}")

    print(f"[3/5] Depositor approves vault for {args.amount} USDC")
    depositor_account = w3.eth.account.from_key(DEPOSITOR_KEY)
    nonce = w3.eth.get_transaction_count(DEPOSITOR)
    approve_tx = usdc.functions.approve(vault_addr, amount_wei).build_transaction(
        {"from": DEPOSITOR, "nonce": nonce, "gas": 100_000, "gasPrice": w3.eth.gas_price}
    )
    signed = w3.eth.account.sign_transaction(approve_tx, DEPOSITOR_KEY)
    w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))

    print(f"[4/5] Depositor deposits {args.amount} USDC into vault")
    vault = w3.eth.contract(address=vault_addr, abi=load_vault_abi())
    deposit_tx = vault.functions.deposit(amount_wei, DEPOSITOR).build_transaction(
        {
            "from": DEPOSITOR,
            "nonce": w3.eth.get_transaction_count(DEPOSITOR),
            "gas": 300_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = w3.eth.account.sign_transaction(deposit_tx, DEPOSITOR_KEY)
    w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))

    print(f"[5/5] Vault state")
    print(f"       totalAssets:  {vault.functions.totalAssets().call() / 1e6:,.2f} USDC")
    print(f"       totalSupply:  {vault.functions.totalSupply().call() / 1e6:,.2f} sVAULT")
    print(f"       positionOpen: {vault.functions.positionOpen().call()}")


if __name__ == "__main__":
    main()
