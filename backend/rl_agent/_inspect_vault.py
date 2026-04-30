"""Quick read-only check of the HypeScanVault state on Base Sepolia."""
from __future__ import annotations
import os, sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

RPC = "https://sepolia.base.org"
VAULT = Web3.to_checksum_address(sys.argv[1] if len(sys.argv) > 1
    else "0xdf57590D27f02BcFA8522d4a59E07Ca7a31b9a6a")

ABI = [
    {"inputs": [], "name": "agent", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "asset", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "swapRouter", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "positionOpen", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "owner", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalAssets", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalSupply", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]
ERC20 = [{"inputs":[{"name":"a","type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
         {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
         {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}]

w3 = Web3(Web3.HTTPProvider(RPC))
v = w3.eth.contract(address=VAULT, abi=ABI)
print(f"vault:        {VAULT}")
print(f"  owner:      {v.functions.owner().call()}")
print(f"  agent:      {v.functions.agent().call()}")
asset = v.functions.asset().call()
print(f"  asset:      {asset}")
print(f"  router:     {v.functions.swapRouter().call()}")
print(f"  posOpen:    {v.functions.positionOpen().call()}")
print(f"  totalAssets:{v.functions.totalAssets().call()}")
print(f"  totalSupply:{v.functions.totalSupply().call()}")

usdc = w3.eth.contract(address=asset, abi=ERC20)
sym = usdc.functions.symbol().call()
dec = usdc.functions.decimals().call()
bal = usdc.functions.balanceOf(VAULT).call()
print(f"  vault {sym}:  {bal / (10**dec):.6f}")

key = os.getenv("AGENT_PRIVATE_KEY")
if key:
    me = w3.eth.account.from_key(key).address
    mybal = usdc.functions.balanceOf(me).call()
    print(f"  my wallet:  {me}  (USDC: {mybal/(10**dec):.6f})")
