"""
AEGIS — Safety Validator (Zone 1 / Trench)

Enforces NERC CIP safety preconditions, sequencing rules, and interlocks
before TRITON executes each step. Can veto any command at any point.

Safety checks performed:
  GET_STATUS       → always passes
  SIMULATE_SWITCH  → always passes (diagnostic, no physical effect)
  OPEN_BREAKER     → zone must be FAULT, asset must be CLOSED,
                     SIMULATE_SWITCH must have run in last 120s
  CLOSE_BREAKER    → asset must be OPEN
  RESTART_CONTROLLER → ALWAYS vetoed (not in RBAC, too destructive)

AEGIS wakes before every TRITON step. If it vetoes, TRITON stops immediately
and LEVIER handles rollback.
"""
import time
from datetime import datetime


class AEGIS:
    NAME = "AEGIS"
    ZONE = "Zone 1 — Trench"
    ROLE = "Safety Validator"
    DESCRIPTION = "Enforces NERC CIP interlocks. Validates every step before TRITON executes."

    def __init__(self):
        self._active        = False
        self._veto_active   = False
        self._last_check    = None
        self._last_sim_time = {}   # asset_id → epoch of last SIMULATE_SWITCH

    @property
    def active(self) -> bool:
        return self._active

    @property
    def veto_active(self) -> bool:
        return self._veto_active

    def validate(self, command: str, asset_id: str, zone: str,
                 assets: dict, zones: dict) -> dict:
        """
        Run all safety preconditions for a single TRITON step.
        Returns: {passed, checks, veto_reason, validated_by}
        If passed=False → TRITON must NOT execute this step.
        """
        self._active      = True
        self._veto_active = False
        checks = []
        veto_reason = None
        now = time.time()

        asset = assets.get(asset_id, {})
        zone_data = zones.get(zone, {})

        # ── Check: RESTART_CONTROLLER is always blocked ────────────────────
        if command == "RESTART_CONTROLLER":
            veto_reason = "RESTART_CONTROLLER is permanently blocked — not in RBAC scope"
            checks.append({"check": "RBAC scope", "passed": False, "detail": veto_reason})

        # ── Check: OPEN_BREAKER preconditions ─────────────────────────────
        elif command == "OPEN_BREAKER":
            # 1. Zone must be FAULT
            zone_health = zone_data.get("health", "HEALTHY")
            if zone_health != "FAULT":
                veto_reason = f"Zone {zone} is {zone_health} — OPEN_BREAKER only justified in FAULT zone"
                checks.append({"check": "Zone health", "passed": False, "detail": veto_reason})
            else:
                checks.append({"check": "Zone health", "passed": True, "detail": f"{zone} is FAULT — correct"})

            # 2. Asset must be CLOSED (can't open what's already open)
            asset_state = asset.get("state", "UNKNOWN")
            if asset_state != "CLOSED":
                r = f"{asset_id} is {asset_state} — must be CLOSED to open"
                veto_reason = veto_reason or r
                checks.append({"check": "Asset state", "passed": False, "detail": r})
            else:
                checks.append({"check": "Asset state", "passed": True, "detail": f"{asset_id} is CLOSED — correct"})

            # 3. SIMULATE_SWITCH must have run in last 120s (NERC CIP SOP)
            last_sim = self._last_sim_time.get(asset_id, 0)
            sim_age  = now - last_sim
            if sim_age > 120:
                r = f"SIMULATE_SWITCH on {asset_id} is {int(sim_age)}s ago (limit: 120s) — re-simulate required"
                veto_reason = veto_reason or r
                checks.append({"check": "Simulation currency", "passed": False, "detail": r})
            else:
                checks.append({"check": "Simulation currency", "passed": True,
                               "detail": f"SIMULATE_SWITCH was {int(sim_age)}s ago — within 120s window"})

        # ── Check: CLOSE_BREAKER preconditions ────────────────────────────
        elif command == "CLOSE_BREAKER":
            asset_state = asset.get("state", "UNKNOWN")
            if asset_state != "OPEN":
                veto_reason = f"{asset_id} is {asset_state} — must be OPEN to close"
                checks.append({"check": "Asset state", "passed": False, "detail": veto_reason})
            else:
                checks.append({"check": "Asset state", "passed": True, "detail": f"{asset_id} is OPEN — correct"})

        # ── GET_STATUS / SIMULATE_SWITCH — always pass ────────────────────
        elif command == "GET_STATUS":
            checks.append({"check": "Read-only", "passed": True, "detail": "GET_STATUS — no preconditions"})

        elif command == "SIMULATE_SWITCH":
            checks.append({"check": "Diagnostic", "passed": True, "detail": "SIMULATE_SWITCH — no preconditions"})
            self._last_sim_time[asset_id] = now   # track sim for next OPEN_BREAKER check

        else:
            veto_reason = f"Unknown command '{command}' — blocked by default"
            checks.append({"check": "Command recognition", "passed": False, "detail": veto_reason})

        passed = veto_reason is None
        if not passed:
            self._veto_active = True

        result = {
            "command":      command,
            "asset_id":     asset_id,
            "zone":         zone,
            "passed":       passed,
            "checks":       checks,
            "veto_reason":  veto_reason,
            "validated_by": self.NAME,
            "timestamp":    datetime.now().isoformat(),
        }
        self._last_check = result
        self._active     = False
        return result

    def reset(self):
        self._veto_active   = False
        self._last_sim_time = {}
        self._last_check    = None

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
            "veto_active": self._veto_active,
            "last_check":  self._last_check,
        }
