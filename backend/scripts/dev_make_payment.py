"""
Dev helper: sends a small USDC payment and prints the tx hash for x402 testing.

Usage:
  ./venv/Scripts/python scripts/dev_make_payment.py \
    --recipient 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 \
    --amount 10000
"""

import argparse

from web3 import Web3

USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

# Anvil default account #2 = our test payer (already funded with USDC by dev_fund_vault)
PAYER = Web3.to_checksum_address("0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC")
PAYER_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default="http://127.0.0.1:8545")
    ap.add_argument("--recipient", required=True, help="address receiving USDC")
    ap.add_argument("--amount", type=int, default=10_000, help="USDC amount in smallest unit (10000 = 0.01 USDC)")
    args = ap.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc))
    assert w3.is_connected(), f"RPC not reachable: {args.rpc}"

    recipient = Web3.to_checksum_address(args.recipient)
    usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)

    payer_bal = usdc.functions.balanceOf(PAYER).call()
    if payer_bal < args.amount:
        raise SystemExit(
            f"payer balance {payer_bal / 1e6:.6f} USDC < required {args.amount / 1e6:.6f} USDC. "
            "Run scripts/dev_fund_vault.py first to fund the payer account."
        )

    tx = usdc.functions.transfer(recipient, args.amount).build_transaction(
        {
            "from": PAYER,
            "nonce": w3.eth.get_transaction_count(PAYER),
            "gas": 100_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }
    )
    signed = w3.eth.account.sign_transaction(tx, PAYER_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"tx_hash:   0x{tx_hash.hex().removeprefix('0x')}")
    print(f"block:     {receipt['blockNumber']}")
    print(f"status:    {'ok' if receipt['status'] == 1 else 'failed'}")
    print(f"recipient: {recipient}  now holds {usdc.functions.balanceOf(recipient).call() / 1e6:.6f} USDC")
    print()
    print("Use in x402 request:")
    print(f"  curl -H 'X-Payment: 0x{tx_hash.hex().removeprefix('0x')}' http://127.0.0.1:8001/signal/base/<token>")


if __name__ == "__main__":
    main()
