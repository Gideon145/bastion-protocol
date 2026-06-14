# SPDX-License-Identifier: MIT
"""On-chain attestation — records detections on Robinhood Chain via DetectionRegistry."""

from __future__ import annotations

import os
from hashlib import sha256

from web3 import Web3

# Minimal ABI for DetectionRegistry
DETECTION_REGISTRY_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "agent", "type": "address"}],
        "name": "registerAgent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "patternHash", "type": "bytes32"},
            {"internalType": "uint8", "name": "severity", "type": "uint8"},
            {"internalType": "uint256", "name": "confidence", "type": "uint256"},
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
        ],
        "name": "recordDetection",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

SEVERITY_MAP = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


def record_onchain(detection: dict) -> str | None:
    """Record a CRITICAL or HIGH detection on-chain via DetectionRegistry.

    The detection is hash-committed: keccak256(pattern, severity, blockNumber, timestamp)
    is stored on-chain, verifiable by anyone via verifyDetection().
    """
    rpc_url = os.environ.get("ROBINHOOD_RPC", "")
    private_key = os.environ.get("AGENT_PRIVATE_KEY", "")
    registry_address = os.environ.get("DETECTION_REGISTRY_ADDRESS", "")

    if not all([rpc_url, private_key, registry_address]):
        print("[ATTEST] Missing env vars — skipping on-chain attestation")
        return None

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)

        registry = w3.eth.contract(
            address=Web3.to_checksum_address(registry_address),
            abi=DETECTION_REGISTRY_ABI,
        )

        pattern = detection.get("pattern", "UNKNOWN")
        severity_str = detection.get("severity", "MEDIUM")
        severity = SEVERITY_MAP.get(severity_str, 0)
        confidence = int(detection.get("confidence", 0))
        evidence = detection.get("evidence", {})

        pattern_hash = Web3.keccak(text=pattern)
        evidence_bytes = str(evidence).encode()
        evidence_hash = Web3.keccak(evidence_bytes)

        # Register agent first (idempotent — safe to call every time)
        try:
            reg_tx = registry.functions.registerAgent(account.address).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "chainId": int(os.environ.get("ROBINHOOD_CHAIN_ID", "46630")),
            })
            signed_reg = account.sign_transaction(reg_tx)
            reg_hash = w3.eth.send_raw_transaction(signed_reg.raw_transaction)
            w3.eth.wait_for_transaction_receipt(reg_hash)
        except Exception:
            pass  # Agent already registered

        # Record detection on-chain
        tx = registry.functions.recordDetection(
            pattern_hash,
            severity,
            confidence,
            evidence_hash,
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": int(os.environ.get("ROBINHOOD_CHAIN_ID", "46630")),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"[ATTEST] Detection #{receipt.get('status', '?')} recorded on-chain: {tx_hash.hex()}")
        return tx_hash.hex()

    except Exception as e:
        print(f"[ATTEST] On-chain attestation failed: {e}")
        return None
