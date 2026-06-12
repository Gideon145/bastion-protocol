# SPDX-License-Identifier: MIT
"""Detection patterns — exploit signatures for Arbitrum DeFi.

Patterns stolen from ChainSight forensic heuristics, adapted for DeFi."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Detection:
    pattern: str
    severity: str       # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float   # 0-100
    evidence: dict      # tx hashes, addresses, amounts
    timestamp: str = field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())


# ── Pattern Detectors ─────────────────────────────────────────────────────


def detect_flash_loan(signals: dict) -> list[Detection]:
    """Detect flash loan attacks: large borrow + multiple swaps in same block."""
    detections = []
    for tx in signals.get("pending_txs", []):
        if tx.get("is_flash_loan") and tx.get("swap_count", 0) >= 3:
            detections.append(Detection(
                pattern="Flash Loan Attack",
                severity="CRITICAL",
                confidence=min(95, 60 + tx.get("amount_usd", 0) / 100000 * 5),
                evidence={
                    "tx_hash": tx.get("hash"),
                    "amount": tx.get("amount"),
                    "swaps": tx.get("swap_count"),
                    "protocols": tx.get("protocols_involved", []),
                },
            ))
    return detections


def detect_oracle_manipulation(signals: dict) -> list[Detection]:
    """Detect oracle manipulation: price deviation > 5% within 60 seconds."""
    detections = []
    prices = signals.get("price_feeds", {})
    for pair, data in prices.items():
        if data.get("deviation_pct", 0) > 5.0:
            detections.append(Detection(
                pattern="Oracle Manipulation",
                severity="CRITICAL",
                confidence=min(95, 50 + data["deviation_pct"] * 5),
                evidence={
                    "pair": pair,
                    "deviation_pct": data["deviation_pct"],
                    "time_window_s": 60,
                    "current_price": data.get("current"),
                    "reference_price": data.get("reference"),
                },
            ))
    return detections


def detect_reentrancy(signals: dict) -> list[Detection]:
    """Detect reentrancy: repeated calls to same contract within single tx."""
    detections = []
    for tx in signals.get("pending_txs", []):
        call_counts = tx.get("call_counts", {})
        for addr, count in call_counts.items():
            if count >= 3 and count <= 20:  # filter infinite loops
                detections.append(Detection(
                    pattern="Reentrancy",
                    severity="HIGH",
                    confidence=min(90, 60 + count * 10),
                    evidence={
                        "tx_hash": tx.get("hash"),
                        "target": addr,
                        "call_count": count,
                    },
                ))
    return detections


def detect_rug_pull(signals: dict) -> list[Detection]:
    """Detect rug pull: liquidity removal + large sell in same block."""
    detections = []
    for tx in signals.get("pending_txs", []):
        if tx.get("liquidity_removed") and tx.get("large_sell"):
            detections.append(Detection(
                pattern="Rug Pull",
                severity="HIGH",
                confidence=85,
                evidence={
                    "tx_hash": tx.get("hash"),
                    "token": tx.get("token_address"),
                    "lp_removed": tx.get("liquidity_removed"),
                    "sell_amount": tx.get("sell_amount"),
                },
            ))
    return detections


def detect_mev_sandwich(signals: dict) -> list[Detection]:
    """Detect MEV sandwich: front-run + victim + back-run pattern."""
    detections = []
    for sandwich in signals.get("sandwich_patterns", []):
        detections.append(Detection(
            pattern="MEV Sandwich",
            severity="MEDIUM",
            confidence=sandwich.get("confidence", 65),
            evidence={
                "front_run": sandwich.get("front_run"),
                "victim": sandwich.get("victim_tx"),
                "back_run": sandwich.get("back_run"),
                "profit_eth": sandwich.get("profit_eth"),
            },
        ))
    return detections


# ── Main detector ─────────────────────────────────────────────────────────

def detect_patterns(signals: dict) -> list[dict]:
    """Run all detection patterns and return list of findings."""
    all_detections = []

    detectors = [
        detect_flash_loan,
        detect_oracle_manipulation,
        detect_reentrancy,
        detect_rug_pull,
        detect_mev_sandwich,
    ]

    for detector in detectors:
        try:
            results = detector(signals)
            for d in results:
                all_detections.append({
                    "pattern": d.pattern,
                    "severity": d.severity,
                    "confidence": d.confidence,
                    "evidence": d.evidence,
                    "timestamp": d.timestamp,
                })
        except Exception:
            pass  # Don't let one detector crash the whole pipeline

    return all_detections
