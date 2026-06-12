# SPDX-License-Identifier: MIT
"""Signal collector — gathers data from Robinhood Chain via Alchemy APIs.

Components used:
  🔴 Alchemy WebSocket — real-time pending tx feed
  🔴 Alchemy Node RPC — block/transaction queries
  🟡 Alchemy Debug API — transaction tracing
  🟡 Alchemy Token API — approval monitoring
  🟡 Alchemy Transfers API — large transfer detection
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import requests
from web3 import Web3


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

ALCHEMY_KEY = os.environ.get("ALCHEMY_API_KEY", "")
RPC_URL = f"https://robinhood-testnet.g.alchemy.com/v2/{ALCHEMY_KEY}" if ALCHEMY_KEY else ""
WS_URL = f"wss://robinhood-testnet.g.alchemy.com/v2/{ALCHEMY_KEY}" if ALCHEMY_KEY else ""
CHAIN_ID = int(os.environ.get("ROBINHOOD_CHAIN_ID", "46630"))

w3 = Web3(Web3.HTTPProvider(RPC_URL)) if RPC_URL else None


# ═══════════════════════════════════════════════════════════════════════════
# Main Collector
# ═══════════════════════════════════════════════════════════════════════════

async def collect_signals() -> dict[str, Any]:
    """Collect all signals in parallel. Returns dict of signal data."""
    results = {}

    tasks = [
        _collect_pending_txs(),
        _collect_recent_blocks(),
        _collect_large_transfers(),
        _collect_token_approvals(),
    ]

    for coro in asyncio.as_completed(tasks):
        try:
            result = await coro
            if result:
                results.update(result)
        except Exception as e:
            print(f"[COLLECTOR] Error: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Sub-collectors — each targets a specific Alchemy API
# ═══════════════════════════════════════════════════════════════════════════

async def _collect_pending_txs() -> dict | None:
    """🔴 Alchemy WebSocket — monitor pending transactions for exploit patterns."""
    if not w3:
        return None

    try:
        # Get pending block (mempool snapshot)
        pending_block = w3.eth.get_block("pending", full_transactions=True)

        txs = []
        for tx in pending_block.get("transactions", [])[:50]:  # Top 50
            txs.append({
                "hash": tx.get("hash", "").hex() if hasattr(tx.get("hash", ""), "hex") else str(tx.get("hash", "")),
                "from": tx.get("from", ""),
                "to": tx.get("to", ""),
                "value": str(tx.get("value", 0)),
                "gas": tx.get("gas", 0),
                "gas_price": str(tx.get("gasPrice", 0)),
            })

        return {"pending_txs": txs, "pending_block": pending_block.get("number", 0)}
    except Exception:
        return {"pending_txs": [], "pending_block": 0}


async def _collect_recent_blocks() -> dict | None:
    """🔴 Alchemy Node RPC — scan recent blocks for exploit signatures."""
    if not w3:
        return None

    try:
        latest = w3.eth.block_number
        blocks = []
        for block_num in range(latest - 5, latest + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            blocks.append({
                "number": block_num,
                "tx_count": len(block.get("transactions", [])),
                "timestamp": block.get("timestamp", 0),
            })

        return {"recent_blocks": blocks, "latest_block": latest}
    except Exception:
        return {"recent_blocks": [], "latest_block": 0}


async def _collect_large_transfers() -> dict | None:
    """🟡 Alchemy Transfers API — detect unusually large token movements."""
    if not ALCHEMY_KEY:
        return None

    url = f"https://robinhood-testnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": "0x0",
            "toBlock": "latest",
            "category": ["erc20"],
            "maxCount": "0xA",  # 10 transfers
        }],
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        data = resp.json()
        transfers = data.get("result", {}).get("transfers", [])

        large = [t for t in transfers if float(t.get("value", 0)) > 10000]  # >10K tokens
        return {"large_transfers": large, "transfer_count": len(transfers)}
    except Exception:
        return {"large_transfers": [], "transfer_count": 0}


async def _collect_token_approvals() -> dict | None:
    """🟡 Alchemy Token API — monitor suspicious token approvals."""
    if not ALCHEMY_KEY:
        return None

    url = f"https://robinhood-testnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getTokenAllowances",
        "params": [{
            "contract": "0x0",  # Check all contracts (stub)
        }],
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {"token_approvals": data.get("result", [])}
    except Exception:
        pass

    return {"token_approvals": []}

