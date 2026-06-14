# SPDX-License-Identifier: MIT
"""Bastion Protocol — Autonomous Exploit Detection Agent for Robinhood Chain.

Architecture:
  COLLECT → SCORE → FSM STATE MACHINE → THREAT REGISTRY → ALERT

4-stage pipeline (stolen from Bento Guard) + FSM (stolen from ArbiGuard):
  NORMAL → ELEVATED → TRIPPED → COOLDOWN

15-second cadence (stolen from PROVUS).

Components used (11 Robinhood/Arbitrum):
  🔴 Chain Deploy, Node RPC, WebSocket, Debug API, Faucet
  🟡 Token API, Transfers API
  🟢 Smart Wallets, Gas Manager, Bundler API
  🔵 Arbitrum Nitro"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.collector import collect_signals
from agent.scorer import score_block, extract_feature_vector, compute_feature_hash
from agent.fsm import FirewallFSM, FSMState
from agent.alerter import send_alert, log_detection
from agent.attest import record_onchain
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Healthcheck HTTP server (for Railway) ──────────────────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        import json as _json
        status = {
            "agent": "Bastion Protocol",
            "chain": "Robinhood (Arbitrum Orbit L2)",
            "chain_id": 46630,
            "pipeline": "COLLECT → SCORE → FSM → THREAT REGISTRY → ALERT",
            "uptime_cycles": self.server.cycle_count if hasattr(self.server, 'cycle_count') else 0,
            "fsm_state": self.server.fsm_state if hasattr(self.server, 'fsm_state') else "NORMAL",
            "current_score": self.server.current_score if hasattr(self.server, 'current_score') else 0.0,
            "threshold": 61,
            "scans_per_minute": 4,
            "contracts": {
                "DetectionRegistry": "0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e",
                "ThreatSignatureRegistry": "0x87E3D9fcfA4eff229A65d045A7C741E49b581187",
            },
            "agent_wallet": "0x94A4365E6B7E79791258A3Fa071824BC2b75a394",
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(_json.dumps(status, indent=2).encode())
    def log_message(self, *args):
        pass

def run_healthcheck(fsm=None):
    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), HealthHandler)
    if fsm:
        server.fsm_state = fsm.state.value
    server.cycle_count = 0
    server.current_score = 0.0
    server.serve_forever()


# ── Configuration ─────────────────────────────────────────────────────────

SCAN_INTERVAL = 15  # seconds (stolen from PROVUS)
SCORE_THRESHOLD = 61  # FSM trip threshold (stolen from ArbiGuard)

# ── Main Loop ─────────────────────────────────────────────────────────────

async def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Bastion Protocol Agent starting...")
    print(f"  Scan interval: {SCAN_INTERVAL}s")
    print(f"  Pipeline: COLLECT → SCORE → FSM → THREAT REGISTRY → ALERT")
    print(f"  FSM states: NORMAL → ELEVATED → TRIPPED → COOLDOWN")
    print(f"  Score threshold: {SCORE_THRESHOLD}")
    print(f"  Chain: Robinhood (46630) via Alchemy")

    # Start healthcheck HTTP server in background thread (for Railway)
    health_server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), HealthHandler)
    health_thread = threading.Thread(target=health_server.serve_forever, daemon=True)
    health_thread.start()
    print(f"  Healthcheck: http://0.0.0.0:{os.environ.get('PORT', '8080')}/")

    fsm = FirewallFSM()
    cycle = 0

    while True:
        cycle += 1
        t_start = time.monotonic()

        try:
            # Stage 1 — COLLECT (parallel, stolen from POH)
            signals = await collect_signals()

            # Stage 2 — SCORE using 8-element feature vector (stolen from ArbiGuard)
            # Wire collector data into the feature vector
            pending_txs = signals.get("pending_txs", [])
            recent_blocks = signals.get("recent_blocks", [])
            large_transfers = signals.get("large_transfers", [])
            approvals = signals.get("approvals", [])

            # Count swaps from pending transactions
            swap_count = len(large_transfers) + len(approvals)

            # Gas anomaly: compare latest block gas to recent average
            gas_anomaly = 1.0
            if recent_blocks and pending_txs:
                avg_gas = sum(
                    int(b.get("tx_count", 0)) for b in recent_blocks
                ) / max(1, len(recent_blocks))
                current_tx_count = len(pending_txs)
                gas_anomaly = max(0.1, current_tx_count / max(1, avg_gas))

            # Liquidity change: derived from large transfer count
            liquidity_change = min(100.0, len(large_transfers) * 5.0)

            block_data = {
                "chain_id": 46630,
                "swap_count": swap_count,
                "oracle_deviation_pct": liquidity_change * 0.1,
                "reentrancy_depth": 0,
                "liquidity_change_pct": liquidity_change,
                "gas_anomaly_multiple": gas_anomaly,
                "time_since_last_pattern": 3600,
            }

            scored = score_block(block_data)
            score = scored["score"]
            feature_hash = scored["feature_hash"]

            # Stage 3 — FSM STATE MACHINE (stolen from ArbiGuard)
            new_state = fsm.evaluate(score, SCORE_THRESHOLD)

            if fsm.should_alert:
                detection = {
                    "pattern": f"FSM_{new_state.value}",
                    "severity": scored["severity"],
                    "confidence": score,
                    "evidence": {
                        "feature_hash": feature_hash,
                        "fsm_state": new_state.value,
                        "score": score,
                        "cycle": cycle,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Stage 4 — ALERT + THREAT REGISTRY
                if new_state == FSMState.TRIPPED:
                    # Publish to ThreatSignatureRegistry (on-chain, gas-sponsored)
                    tx_hash = record_onchain(detection)
                    if tx_hash:
                        print(f"[TRIPPED] Published threat {feature_hash[:16]}... tx={tx_hash[:10]}...")

                if new_state in (FSMState.TRIPPED, FSMState.ELEVATED):
                    await send_alert(detection)

                log_detection(detection)

            # Log state transitions
            if cycle % 4 == 0:  # Every ~60 seconds
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] "
                      f"Cycle {cycle} | State: {fsm.state.value} | Score: {score:.1f}")
                # Update healthcheck endpoint with live stats
                health_server.cycle_count = cycle
                health_server.current_score = round(score, 1)
                health_server.fsm_state = fsm.state.value

        except Exception as e:
            print(f"[ERROR] Cycle {cycle}: {e}")

        elapsed = time.monotonic() - t_start
        sleep_time = max(0, SCAN_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(main())
