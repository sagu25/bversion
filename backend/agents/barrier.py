"""
BARRIER — Policy Enforcement Agent (Zone 4)

The only agent that can ALLOW or DENY commands at the gateway.
TARE decides what mode to set. BARRIER enforces it — no interpretation, no judgment.

TARE instructs: barrier.set_mode("FREEZE")
Gateway calls:  barrier.enforce(command, zone) → (ALLOW/DENY, reason, policy_id)

Never analyzes behavior. Never creates incidents. Only enforces the mode it is given.
"""

READ_ONLY   = {"GET_STATUS"}
DIAG_CMDS   = {"SIMULATE_SWITCH"}
HIGH_IMPACT = {"OPEN_BREAKER", "CLOSE_BREAKER", "RESTART_CONTROLLER", "EMERGENCY_SHUTDOWN"}


class BARRIER:
    NAME = "BARRIER"
    ZONE = "Zone 4"
    ROLE = "Policy Enforcement Agent"
    DESCRIPTION = "Enforces TARE's mode decisions at the command gateway. The sole ALLOW/DENY authority."

    def __init__(self):
        self._mode   = "NORMAL"
        self._active = False

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def active(self) -> bool:
        return self._active

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        """
        TARE instructs BARRIER to change its enforcement mode.
        Instantly takes effect — all subsequent enforce() calls use the new mode.
        """
        self._mode = mode

    def enforce(self, command: str, zone: str = None) -> tuple:
        """
        Evaluate a command against the current enforcement mode.
        Returns (decision, reason, policy_id).
        Wakes on call, sleeps immediately after returning.
        """
        self._active = True
        result       = self._evaluate(command, zone)
        self._active = False
        return result

    def reset(self) -> None:
        self._mode   = "NORMAL"

    # ── Enforcement Logic ──────────────────────────────────────────────────────

    def _evaluate(self, command: str, zone: str) -> tuple:
        m = self._mode

        if m == "NORMAL":
            if command == "RESTART_CONTROLLER":
                return ("DENY",
                        "RESTART_CONTROLLER not in RBAC claims",
                        "POL-RBAC-001")
            return ("ALLOW",
                    "Within RBAC and baseline policy",
                    "POL-NORMAL-001")

        elif m == "FREEZE":
            if command in READ_ONLY:
                return ("ALLOW",
                        "Read-only permitted during FREEZE",
                        "POL-FREEZE-002")
            return ("DENY",
                    "SAFETY HOLD ACTIVE — high-impact operations frozen by TARE",
                    "POL-FREEZE-001")

        elif m == "DOWNGRADE":
            if command in (READ_ONLY | DIAG_CMDS):
                return ("ALLOW",
                        "Diagnostics and simulation permitted in DOWNGRADE",
                        "POL-DOWN-001")
            return ("DENY",
                    "DOWNGRADE mode — operational commands restricted",
                    "POL-DOWN-002")

        elif m == "TIMEBOX_ACTIVE":
            if command == "RESTART_CONTROLLER":
                return ("DENY",
                        "RESTART_CONTROLLER permanently blocked — not in time-box scope",
                        "POL-TIMEBOX-002")
            if command in HIGH_IMPACT:
                return ("ALLOW",
                        "TIME-BOX ACTIVE — within supervisor-approved window",
                        "POL-TIMEBOX-001")
            return ("ALLOW",
                    "TIME-BOX ACTIVE — within approved window",
                    "POL-TIMEBOX-001")

        elif m == "SAFE":
            if command in READ_ONLY:
                return ("ALLOW",
                        "Safe mode — read-only permitted",
                        "POL-SAFE-001")
            return ("DENY",
                    "Safe mode — awaiting operator review before resuming operations",
                    "POL-SAFE-002")

        return ("DENY", "Unknown enforcement mode", "POL-ERR-001")

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
            "mode":        self._mode,
        }
