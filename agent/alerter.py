# SPDX-License-Identifier: MIT
"""Telegram alerter — stolen from World Cup bot."""

from __future__ import annotations

import os
import asyncio
from datetime import datetime


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


async def send_alert(detection: dict) -> bool:
    """Send exploit alert via Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    severity_emoji = {
        "CRITICAL": "🔴🔴",
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "⚪",
    }

    sev = detection.get("severity", "UNKNOWN")
    emoji = severity_emoji.get(sev, "⚪")

    msg = (
        f"{emoji} ARBSHIELD ALERT\n\n"
        f"Pattern: {detection['pattern']}\n"
        f"Severity: {sev}\n"
        f"Confidence: {detection['confidence']:.0f}%\n"
        f"Time: {detection.get('timestamp', datetime.now().isoformat())[:19]}\n\n"
        f"Evidence:\n"
    )
    for k, v in detection.get("evidence", {}).items():
        msg += f"  {k}: {v}\n"

    try:
        from telegram import Bot
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        return True
    except Exception:
        return False


def log_detection(detection: dict):
    """Log detection to local file."""
    log_path = os.path.join(os.path.dirname(__file__), "..", "detections.log")
    with open(log_path, "a") as f:
        f.write(f"[{detection['timestamp']}] {detection['severity']} | "
                f"{detection['pattern']} | {detection['confidence']:.0f}%\n")
