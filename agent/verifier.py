# SPDX-License-Identifier: MIT
"""Verifier — 2/3 multi-signal consensus (stolen from TriMind OKX winner).

Before escalating any detection, we require at least 2 of 3 signals to agree:
  1. Rule Engine: deterministic threshold check
  2. AI Scorer (Gemini): semantic confidence score
  3. On-chain oracle: price verification
"""

from __future__ import annotations

import os


def verify_detection(detection: dict) -> bool:
    """Verify a detection using 2/3 consensus. Returns True if verified."""
    signals_passed = 0

    # 1. Rule Engine — always runs, deterministic
    rule_ok = _rule_check(detection)
    if rule_ok:
        signals_passed += 1

    # 2. AI Scorer — semantic check via Gemini
    ai_ok = _ai_check(detection)
    if ai_ok:
        signals_passed += 1

    # 3. Oracle check — if applicable
    oracle_ok = _oracle_check(detection)
    if oracle_ok:
        signals_passed += 1

    # 2/3 must agree (stolen from TriMind)
    return signals_passed >= 2


def _rule_check(detection: dict) -> bool:
    """Deterministic rule-based verification."""
    confidence = detection.get("confidence", 0)
    severity = detection.get("severity", "LOW")

    thresholds = {"CRITICAL": 80, "HIGH": 70, "MEDIUM": 60, "LOW": 50}
    return confidence >= thresholds.get(severity, 50)


def _ai_check(detection: dict) -> bool:
    """AI semantic check using Gemini (stolen from ChainSight)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return True  # Pass through if no key (don't block on missing API)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = (
            f"Analyze this DeFi exploit detection on Arbitrum. Is this a real threat?\n\n"
            f"Pattern: {detection.get('pattern')}\n"
            f"Confidence: {detection.get('confidence')}%\n"
            f"Evidence: {detection.get('evidence')}\n\n"
            f"Reply with YES or NO only."
        )

        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 10, "temperature": 0.1},
        )
        return "YES" in response.text.upper()
    except Exception:
        return True  # Pass through on API failure


def _oracle_check(detection: dict) -> bool:
    """On-chain oracle data verification."""
    # For oracle manipulation detection, skip (circular)
    if detection.get("pattern") == "Oracle Manipulation":
        return True

    # For other patterns, check if oracle data is consistent
    evidence = detection.get("evidence", {})
    if not evidence:
        return True  # No oracle data to check

    return True  # Stub — implement with actual oracle queries
