"""
LEVIER — Rollback & Recovery Agent (Zone 1 / Trench)

Wakes only when TRITON fails, AEGIS vetoes, or TEMPEST triggers a freeze.
Executes rollback steps from the NAVIS plan in reverse to restore safe state.
Never initiates new actions — only stabilises and recovers.

Rollback steps are produced by NAVIS (e.g., CLOSE_BREAKER if OPEN_BREAKER ran).
LEVIER executes them via the same engine callback TRITON uses.
"""
import os
from datetime import datetime

try:
    from blueverse_client import get_client as _get_bv_client
    _BV_OK = bool(os.environ.get("BLUEVERSE_CLIENT_ID", ""))
except Exception:
    _get_bv_client = None
    _BV_OK = False


class LEVIER:
    NAME = "LEVIER"
    ZONE = "Zone 1 — Trench"
    ROLE = "Rollback & Recovery Agent"
    DESCRIPTION = "Reverts executed steps to restore safe state. Only wakes on failure."

    def __init__(self):
        self._active        = False
        self._last_recovery = None
        self._execute_fn    = None

    @property
    def active(self) -> bool:
        return self._active

    def arm(self, execute_fn) -> None:
        """Give LEVIER the execute callback so it can revert steps if needed."""
        self._execute_fn = execute_fn

    def rollback(self, rollback_steps: list, completed_steps: list = None) -> dict:
        """
        Execute rollback steps in order to undo what TRITON completed.
        rollback_steps : from NAVIS plan [{command, asset_id, zone, rationale}]
        completed_steps: which TRITON steps actually ran (only roll those back)

        Returns a recovery report.
        """
        self._active = True
        completed_steps = completed_steps or []
        results = []
        errors  = []

        # Only roll back steps that actually executed
        # Match by asset_id — if TRITON ran OPEN_BREAKER on BRK-301, LEVIER runs CLOSE_BREAKER on BRK-301
        executed_assets = {s.get("asset_id") for s in completed_steps if s.get("status") == "EXECUTED"}
        steps_to_run = [s for s in rollback_steps if s.get("asset_id") in executed_assets] if executed_assets else rollback_steps

        for step in steps_to_run:
            cmd      = step.get("command")
            asset_id = step.get("asset_id")
            zone     = step.get("zone")

            if not cmd or not asset_id or not zone:
                errors.append(f"Incomplete rollback step: {step}")
                continue

            try:
                if self._execute_fn:
                    result = self._execute_fn(cmd, asset_id, zone)
                    results.append({
                        "command":   cmd,
                        "asset_id":  asset_id,
                        "zone":      zone,
                        "decision":  result.get("decision"),
                        "status":    "ROLLED_BACK",
                    })
                else:
                    results.append({
                        "command":  cmd,
                        "asset_id": asset_id,
                        "zone":     zone,
                        "status":   "NO_EXECUTE_FN",
                    })
            except Exception as e:
                errors.append(f"{cmd} on {asset_id}: {e}")

        recovery = {
            "steps_planned":  len(steps_to_run),
            "steps_executed": len(results),
            "results":        results,
            "errors":         errors,
            "status":         "COMPLETE" if not errors else "PARTIAL",
            "recovered_by":   self.NAME,
            "timestamp":      datetime.now().isoformat(),
        }
        # Enhance recovery report with BlueVerse
        if _BV_OK and _get_bv_client:
            try:
                message = (
                    f"LEVIER rollback complete. Steps planned: {recovery['steps_planned']}, "
                    f"executed: {recovery['steps_executed']}, status: {recovery['status']}. "
                    f"Errors: {recovery['errors'] or 'none'}. "
                    f"In 1-2 sentences, report the rollback outcome to the supervisor."
                )
                bv_report = _get_bv_client().invoke_safe("LEVIER", message, fallback="")
                if bv_report:
                    recovery["bv_report"] = bv_report
            except Exception:
                pass

        self._last_recovery = recovery
        self._active        = False
        return recovery

    def reset(self):
        self._active        = False
        self._last_recovery = None
        self._execute_fn    = None

    def status(self) -> dict:
        return {
            "name":          self.NAME,
            "zone":          self.ZONE,
            "role":          self.ROLE,
            "description":   self.DESCRIPTION,
            "active":        self._active,
            "last_recovery": self._last_recovery,
        }
