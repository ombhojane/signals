"""
Dev helper: mint USDC into an arbitrary Anvil account via whale impersonation.

Usage:
  ./venv/Scripts/python scripts/dev_fund_account.py \
    --to 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC --amount 100
"""

import argparse

from web3 import Web3

USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
USDC_WHALE = Web3.to_checksum_address("0xd0b53D9277642d899DF5C87A3966A349A798F224")

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
    ap.add_argument("--to", required=True, help="recipient address")
    ap.add_argument("--amount", type=int, default=100, help="USDC amount (whole units)")
    args = ap.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc))
    assert w3.is_connected(), f"RPC not reachable: {args.rpc}"

    to = Web3.to_checksum_address(args.to)
    amount_wei = args.amount * 10**6

    w3.provider.make_request("anvil_setBalance", [USDC_WHALE, hex(10**18)])
    w3.provider.make_request("anvil_impersonateAccount", [USDC_WHALE])

    usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    tx_hash = usdc.functions.transfer(to, amount_wei).transact({"from": USDC_WHALE})
    w3.eth.wait_for_transaction_receipt(tx_hash)

    w3.provider.make_request("anvil_stopImpersonatingAccount", [USDC_WHALE])

    bal = usdc.functions.balanceOf(to).call()
    print(f"funded {to} with {args.amount} USDC; balance now {bal / 1e6:,.6f} USDC")


if __name__ == "__main__":
    main()
