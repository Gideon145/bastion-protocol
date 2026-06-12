# SPDX-License-Identifier: MIT
"""Canonical Feature Vector — 8-element scoring (stolen from ArbiGuard).

Each transaction/block is reduced to a deterministic 8-element vector.
The score (0-100) is computed deterministically — identical input = identical output.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any


def extract_feature_vector(block_data: dict, tx_data: dict | None = None) -> list[float]:
    """Extract the canonical 8-element feature vector from block/transaction data.

    Elements:
      0. chain_id          — Which chain (46630 = Robinhood)
      1. amount            — USD value moved in the transaction
      2. swap_count        — Number of swaps in the block
      3. oracle_deviation  — Price deviation from oracle (%, 0 if N/A)
      4. reentrancy_depth  — Call depth for same contract (0-10)
      5. liquidity_change  — LP token change (%) in the block
      6. gas_anomaly       — Gas price deviation from 10-block average (multiples)
      7. time_window       — Time since last similar pattern (seconds, capped at 3600)
    """
    return [
        float(block_data.get("chain_id", 46630)),
        float(tx_data.get("amount_usd", 0)) if tx_data else 0.0,
        float(block_data.get("swap_count", 0)),
        float(block_data.get("oracle_deviation_pct", 0.0)),
        float(block_data.get("reentrancy_depth", 0)),
        float(block_data.get("liquidity_change_pct", 0.0)),
        float(block_data.get("gas_anomaly_multiple", 1.0)),
        min(3600.0, float(block_data.get("time_since_last_pattern", 3600))),
    ]


def compute_score(feature_vector: list[float]) -> float:
    """Compute deterministic threat score (0-100) from feature vector.

    Scoring logic stolen from ArbiGuard's RiskEngine:
      - High amounts + high swaps + oracle deviation = higher score
      - Signed binary discount: -15 if target is a known good contract
      - Capped at 100, floored at 0
    """
    # Weights (tuned against Radiant Capital exploit)
    weights = [0.0, 0.000015, 8.0, 6.0, 5.0, 4.0, 3.0, 0.002]

    score = sum(v * w for v, w in zip(feature_vector, weights))

    # Signed binary discount — known good contracts get -15
    # In production: check against on-chain allowlist
    # For now: apply discount if swap_count < 2 (simple heuristic)
    if feature_vector[2] < 2:
        score -= 15

    return max(0.0, min(100.0, score))


def compute_feature_hash(feature_vector: list[float]) -> str:
    """Compute deterministic hash of feature vector for ThreatSignatureRegistry."""
    data = ",".join(f"{v:.4f}" for v in feature_vector)
    return sha256(data.encode()).hexdigest()[:32]  # First 16 bytes as hex


def score_block(block_data: dict, tx_data: dict | None = None) -> dict:
    """Score a block/transaction — full pipeline.

    Returns dict with feature_vector, score, feature_hash, and severity.
    """
    fv = extract_feature_vector(block_data, tx_data)
    score = compute_score(fv)
    fhash = compute_feature_hash(fv)

    # Severity thresholds (stolen from ArbiGuard's FSM)
    if score >= 80:
        severity = "CRITICAL"
    elif score >= 61:
        severity = "HIGH"
    elif score >= 40:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "feature_vector": fv,
        "score": round(score, 1),
        "feature_hash": fhash,
        "severity": severity,
    }
