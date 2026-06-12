"""Deploy Bastion Protocol contracts to Robinhood Chain testnet."""
import json
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web3 import Web3

# Load .env
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

RPC_URL = os.environ.get("ROBINHOOD_RPC", "https://rpc.testnet.chain.robinhood.com")
PRIVATE_KEY = os.environ.get("AGENT_PRIVATE_KEY", "")
CHAIN_ID = 46630

if not PRIVATE_KEY:
    print("❌ AGENT_PRIVATE_KEY not set in .env")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
acct = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Deployer: {acct.address}")
print(f"Balance: {w3.eth.get_balance(acct.address) / 1e18:.4f} ETH")
print(f"Chain ID: {w3.eth.chain_id}")

# ── Contracts to deploy ───────────────────────────────────────────────────

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"

DEPLOYMENTS = []

# 1. ThreatSignatureRegistry
tsr_path = CONTRACTS_DIR / "ThreatSignatureRegistry.sol"
if tsr_path.exists():
    print(f"\nDeploying ThreatSignatureRegistry...")
    # Compile with solcx or use pre-compiled ABI
    # For now, deploy bytecode directly
    try:
        from solcx import compile_standard, install_solc
        install_solc("0.8.26")
        
        with open(tsr_path) as f:
            source = f.read()
        
        compiled = compile_standard({
            "language": "Solidity",
            "sources": {"ThreatSignatureRegistry.sol": {"content": source}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}},
        }, solc_version="0.8.26")
        
        contract = compiled["contracts"]["ThreatSignatureRegistry.sol"]["ThreatSignatureRegistry"]
        abi = contract["abi"]
        bytecode = contract["evm"]["bytecode"]["object"]
        
        # Deploy
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = Contract.constructor().build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 2000000,
            "gasPrice": w3.eth.gas_price,
            "chainId": CHAIN_ID,
        })
        
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"  ✅ Deployed: {receipt.contractAddress}")
        print(f"  TX: {tx_hash.hex()}")
        DEPLOYMENTS.append({"name": "ThreatSignatureRegistry", "address": receipt.contractAddress, "tx": tx_hash.hex()})
        
    except ImportError:
        print("  ⚠️ solcx not installed. Install with: pip install py-solc-x")
        print("  Deploy manually via Remix or Foundry")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
else:
    print(f"  ⚠️ {tsr_path} not found")

# 2. DetectionRegistry
dr_path = CONTRACTS_DIR / "DetectionRegistry.sol"
if dr_path.exists():
    print(f"\nDeploying DetectionRegistry...")
    try:
        from solcx import compile_standard
        
        with open(dr_path) as f:
            source = f.read()
        
        compiled = compile_standard({
            "language": "Solidity",
            "sources": {"DetectionRegistry.sol": {"content": source}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}},
        }, solc_version="0.8.26")
        
        contract = compiled["contracts"]["DetectionRegistry.sol"]["DetectionRegistry"]
        abi = contract["abi"]
        bytecode = contract["evm"]["bytecode"]["object"]
        
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = Contract.constructor().build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 2000000,
            "gasPrice": w3.eth.gas_price,
            "chainId": CHAIN_ID,
        })
        
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"  ✅ Deployed: {receipt.contractAddress}")
        print(f"  TX: {tx_hash.hex()}")
        DEPLOYMENTS.append({"name": "DetectionRegistry", "address": receipt.contractAddress, "tx": tx_hash.hex()})
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")

# ── Save deployments ──────────────────────────────────────────────────────

if DEPLOYMENTS:
    deploy_file = Path(__file__).resolve().parent.parent / "deployments.json"
    with open(deploy_file, "w") as f:
        json.dump(DEPLOYMENTS, f, indent=2)
    print(f"\n📜 Saved to {deploy_file}")
    for d in DEPLOYMENTS:
        print(f"  {d['name']}: {d['address']}")
