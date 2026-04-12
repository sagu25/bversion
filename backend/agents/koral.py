"""
KORAL — Telemetry Observer (Zone 3 / Reef)

Continuously records every command, timestamp, zone, and asset ID.
Provides the raw telemetry foundation for all analysis agents.
Never interprets. Never acts. Only observes and stores.

Wake pattern: active for the duration of observe(), sleeps immediately after.
"""
import time
from collections import deque
from datetime import datetime


class KORAL:
    NAME = "KORAL"
    ZONE = "Zone 3 — Reef"
    ROLE = "Telemetry Observer"
    DESCRIPTION = "Records every command, zone, and timestamp. Trusted telemetry baseline."

    def __init__(self):
        self._command_history = deque(maxlen=100)
        self._burst_window    = deque(maxlen=50)   # stores epoch timestamps only
        self._zone_access_log = []
        self._identity_log    = []                 # identity action attempts
        self._active          = False
        self._total_observed  = 0

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def active(self) -> bool:
        return self._active

    def observe(self, record: dict) -> None:
        """
        Record a new command event.
        Called on every command before any analysis begins.
        record must contain: id, ts, ts_epoch, command, asset_id, zone
        """
        self._active = True
        self._command_history.append(record)
        self._burst_window.append(record.get("ts_epoch", time.time()))
        self._zone_access_log.append(record)
        self._total_observed += 1
        self._active = False   # back to sleep

    def get_session(self, n: int = 30) -> list:
        """Return last N commands from the session history."""
        return list(self._command_history)[-n:]

    def get_burst_window(self) -> deque:
        """Return the raw timestamp deque used for burst-rate analysis."""
        return self._burst_window

    def get_zone_log(self, n: int = 20) -> list:
        """Return last N zone access records for the observability panel."""
        return self._zone_access_log[-n:]

    def log_action(self, principal: str, action: str, target_zone: str) -> dict:
        """
        Log an identity action attempt for policy evaluation.
        Called before TARE checks the identity policy.
        """
        try:
            from identity_registry import classify_action
            action_type = classify_action(action)
        except Exception:
            action_type = "UNKNOWN"

        record = {
            "principal":   principal,
            "action":      action,
            "action_type": action_type,
            "target_zone": target_zone,
            "timestamp":   datetime.now().isoformat(),
        }
        self._identity_log.append(record)
        return record

    def get_identity_log(self, n: int = 20) -> list:
        """Return last N identity action log entries."""
        return self._identity_log[-n:]

    def clear(self) -> None:
        self._command_history.clear()
        self._burst_window.clear()
        self._zone_access_log.clear()
        self._identity_log.clear()
        self._total_observed = 0

    def status(self) -> dict:
        return {
            "name":           self.NAME,
            "zone":           self.ZONE,
            "role":           self.ROLE,
            "description":    self.DESCRIPTION,
            "active":         self._active,
            "session_length": len(self._command_history),
            "total_observed": self._total_observed,
        }
