# SPDX-License-Identifier: MIT
"""FSM State Machine — stolen from ArbiGuard (aliveevie).

States: NORMAL → ELEVATED → TRIPPED → COOLDOWN

- NORMAL: No threats detected. Agent scanning passively.
- ELEVATED: Suspicious activity detected. Increased monitoring frequency.
- TRIPPED: Threat confirmed. Publish to ThreatSignatureRegistry, trigger alerts.
- COOLDOWN: Recovery period after tripping. Gradual return to NORMAL.
"""

from __future__ import annotations

from enum import Enum
from datetime import datetime, timedelta


class FSMState(Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    TRIPPED = "TRIPPED"
    COOLDOWN = "COOLDOWN"


class FirewallFSM:
    """Hysteresis breaker — prevents flip-flopping between states."""

    def __init__(self):
        self.state = FSMState.NORMAL
        self.elevated_since: datetime | None = None
        self.tripped_at: datetime | None = None
        self.cooldown_until: datetime | None = None
        self.score_history: list[float] = []  # Last 10 scores

    def evaluate(self, score: float, threshold: float = 61.0) -> FSMState:
        """Evaluate a detection score and transition FSM accordingly.

        Args:
            score: Detection confidence score (0-100)
            threshold: Score that triggers state transition (default 61)

        Returns:
            New FSM state after evaluation
        """
        self.score_history.append(score)
        if len(self.score_history) > 10:
            self.score_history.pop(0)

        now = datetime.now()

        # COOLDOWN → NORMAL transition
        if self.state == FSMState.COOLDOWN:
            if self.cooldown_until and now >= self.cooldown_until:
                self.state = FSMState.NORMAL
                self.cooldown_until = None
                self.tripped_at = None
            return self.state

        # TRIPPED → COOLDOWN transition
        if self.state == FSMState.TRIPPED:
            # After tripping, go to cooldown for 5 minutes
            self.state = FSMState.COOLDOWN
            self.cooldown_until = now + timedelta(minutes=5)
            self.elevated_since = None
            return self.state

        # NORMAL → ELEVATED: score crosses threshold
        if self.state == FSMState.NORMAL and score >= threshold:
            self.state = FSMState.ELEVATED
            self.elevated_since = now
            return self.state

        # ELEVATED → TRIPPED: sustained elevated across blocks
        if self.state == FSMState.ELEVATED:
            if score < threshold:
                # Score dropped below threshold — back to NORMAL
                if self._all_recent_below(threshold):
                    self.state = FSMState.NORMAL
                    self.elevated_since = None
                return self.state

            # Sustained: elevated for 3+ consecutive scores → TRIP
            recent_above = sum(1 for s in self.score_history[-5:] if s >= threshold)
            if recent_above >= 3:
                self.state = FSMState.TRIPPED
                self.tripped_at = now
                return self.state

        return self.state

    def _all_recent_below(self, threshold: float) -> bool:
        """Check if all recent scores are below threshold."""
        recent = self.score_history[-5:]
        return all(s < threshold for s in recent) if recent else True

    @property
    def is_tripped(self) -> bool:
        return self.state == FSMState.TRIPPED

    @property
    def should_alert(self) -> bool:
        return self.state in (FSMState.TRIPPED, FSMState.ELEVATED)
