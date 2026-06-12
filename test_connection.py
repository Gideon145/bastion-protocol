# SPDX-License-Identifier: MIT
"""Connection test — verify all Robinhood Chain + Alchemy APIs are reachable."""

import os
import sys
from pathlib import Path

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

CHECKS_PASSED = 0
CHECKS_TOTAL = 0


def check(name: str, condition: bool, detail: str = ""):
    global CHECKS_PASSED, CHECKS_TOTAL
    CHECKS_TOTAL += 1
    if condition:
        CHECKS_PASSED += 1
        print(f"  ✅ {name}: {detail}")
    else:
        print(f"  ❌ {name}: {detail}")
    return condition


print("Bastion Protocol — Robinhood Chain Connection Test\n")

# 1. Alchemy API key
key = os.environ.get("ALCHEMY_API_KEY", "")
check("Alchemy API key configured", bool(key) and len(key) > 10, "Set ALCHEMY_API_KEY in .env")

# 2. RPC Connection
if key:
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(f"https://robinhood-testnet.g.alchemy.com/v2/{key}"))
        connected = w3.is_connected()
        check("RPC connection", connected, f"Chain ID: {w3.eth.chain_id if connected else 'N/A'}")
        if connected:
            block = w3.eth.block_number
            check("Latest block", block > 0, f"Block #{block}")
            balance = w3.eth.get_balance("0x0000000000000000000000000000000000000000")
            check("ETH balance query", True, "RPC responding")
    except Exception as e:
        check("RPC connection", False, str(e)[:80])

# 3. Alchemy-specific APIs
if key:
    import requests
    url = f"https://robinhood-testnet.g.alchemy.com/v2/{key}"

    # Transfer API
    try:
        resp = requests.post(url, json={
            "jsonrpc": "2.0", "id": 1, "method": "alchemy_getAssetTransfers",
            "params": [{"fromBlock": "0x0", "toBlock": "latest", "category": ["erc20"], "maxCount": "0x1"}],
        }, timeout=5)
        ok = resp.status_code == 200 and "result" in resp.json()
        check("Transfers API", ok, "alchemy_getAssetTransfers")
    except Exception as e:
        check("Transfers API", False, str(e)[:60])

    # Token API
    try:
        resp = requests.post(url, json={
            "jsonrpc": "2.0", "id": 1, "method": "alchemy_getTokenMetadata",
            "params": ["0xdAC17F958D2ee523a2206206994597C13D831ec7"],
        }, timeout=5)
        ok = resp.status_code == 200
        check("Token API", ok, "alchemy_getTokenMetadata")
    except Exception as e:
        check("Token API", False, str(e)[:60])

# 4. Gemini API
gemini_key = os.environ.get("GEMINI_API_KEY", "")
check("Gemini API key configured", bool(gemini_key) and len(gemini_key) > 10, "Set GEMINI_API_KEY in .env")

# 5. Telegram
tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
check("Telegram configured", bool(tg_token) and bool(tg_chat), "Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID")

# 6. Agent wallet
pk = os.environ.get("AGENT_PRIVATE_KEY", "")
addr = os.environ.get("AGENT_ADDRESS", "")
check("Agent wallet configured", bool(pk) and bool(addr), "Set AGENT_PRIVATE_KEY + AGENT_ADDRESS")

# Summary
print(f"\n{'='*50}")
print(f"Results: {CHECKS_PASSED}/{CHECKS_TOTAL} checks passed")
if CHECKS_PASSED == CHECKS_TOTAL:
    print("All systems go! Run: python -m agent.main")
else:
    print(f"Fix {CHECKS_TOTAL - CHECKS_PASSED} issues above, then retry.")
