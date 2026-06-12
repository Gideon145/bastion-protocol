# SPDX-License-Identifier: MIT
"""On-chain attestation — records detections on Arbitrum (stolen from DAEMON/PROVUS)."""

from __future__ import annotations

import os
from hashlib import sha256


def record_onchain(detection: dict) -> str | None:
    """Record a CRITICAL detection on-chain via DetectionRegistry."""
    rpc_url = os.environ.get("ARB_RPC_URL", "")
    private_key = os.environ.get("PRIVATE_KEY", "")
    registry_address = os.environ.get("DETECTION_REGISTRY_ADDRESS", "")

    if not all([rpc_url, private_key, registry_address]):
        return None

    # Generate evidence hash
    evidence_str = str(detection.get("evidence", {}))
    evidence_hash = sha256(evidence_str.encode()).hexdigest()

    # Pattern hash
    pattern_hash = sha256(detection.get("pattern", "").encode()).hexdigest()

    # Stub — implement with ethers.js / web3.py
    # tx = registry.recordDetection(
    #     pattern_hash,
    #     severity_to_uint(detection["severity"]),
    #     int(detection["confidence"]),
    #     evidence_hash,
    # )
    # return tx.hash

    return None
