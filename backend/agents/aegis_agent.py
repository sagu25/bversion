"""
AEGIS — Safety Validator (Zone 1 / Trench)

Enforces safety preconditions, sequencing rules, and interlocks before
any execution step proceeds. Can veto or stop actions that violate
safety or policy constraints — even mid-execution.

This is the final safety gate before any physical action reaches a grid asset.
AEGIS can halt TRITON at any point if a safety condition is violated.

Wake pattern: activated immediately before each TRITON execution step.
Arms before the step. Disarms after. Can interrupt at any point.

Phase 2 scope — stub implemented, full interlock engine pending.

Note: Named aegis_agent.py to avoid conflict with the top-level aegis_engine.py
"""


class AEGIS:
    NAME = "AEGIS"
    ZONE = "Zone 1 — Trench"
    ROLE = "Safety Validator"
    DESCRIPTION = "Enforces safety preconditions and interlocks. Can veto any execution step."

    def __init__(self):
        self._active       = False
        self._last_check   = None
        self._veto_active  = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def veto_active(self) -> bool:
        return self._veto_active

    def validate(self, command: str, asset_id: str, zone: str,
                 assets: dict, zones: dict) -> dict:
        """
        Check all safety preconditions before TRITON executes a command.
        Returns validation result. If passed=False, TRITON must not proceed.
        Full implementation: Phase 2 (real NERC CIP interlock checks).
        """
        self._active = True
        self._veto_active = False

        result = {
            "command":      command,
            "asset_id":     asset_id,
            "zone":         zone,
            "passed":       True,       # stub always passes — Phase 2 adds real checks
            "checks":       [],
            "veto_reason":  None,
            "validated_by": self.NAME,
            "note":         "Safety interlock stub — Phase 2.",
        }

        self._last_check = result
        self._active     = False
        return result

    def veto(self, reason: str) -> None:
        """
        Issue an immediate veto — halts TRITON regardless of permit.
        Called when a mid-execution safety condition is violated.
        """
        self._veto_active = True
        self._last_check  = {"veto_reason": reason, "validated_by": self.NAME}

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
            "phase":       "Phase 2 — Stub",
            "veto_active": self._veto_active,
            "last_check":  self._last_check,
        }
