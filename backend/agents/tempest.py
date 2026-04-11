"""
TEMPEST — Session & Tempo Monitor (Zone 1 / Trench)

Arms when TRITON begins executing. Watches every step during live execution.
Can trigger an immediate freeze if behaviour becomes unsafe mid-operation.

Violations that trigger a freeze:
  - Steps executing too fast (< MIN_INTER_STEP_SECONDS between steps)
  - Too many steps in one session (> MAX_STEPS_PER_SESSION)
  - Command deviates from the approved NAVIS plan
  - Too many retries on the same step (> MAX_RETRIES_PER_STEP)

TEMPEST is the last line of defence. Even an approved, time-boxed session
can be frozen if execution pace becomes abnormal.
"""
import os
import time
from datetime import datetime

try:
    from blueverse_client import get_client as _get_bv_client
    _BV_OK = bool(os.environ.get("BLUEVERSE_CLIENT_ID", ""))
except Exception:
    _get_bv_client = None
    _BV_OK = False


MIN_INTER_STEP_SECONDS = 1.0
MAX_STEPS_PER_SESSION  = 15
MAX_RETRIES_PER_STEP   = 2


class TEMPEST:
    NAME = "TEMPEST"
    ZONE = "Zone 1 — Trench"
    ROLE = "Session & Tempo Monitor"
    DESCRIPTION = "Monitors execution pace mid-operation. Can freeze a session if tempo is violated."

    def __init__(self):
        self._active       = False
        self._armed        = False
        self._step_times   = []
        self._step_log     = []
        self._retry_counts = {}   # command → count
        self._freeze_fn    = None
        self._plan_steps   = []   # approved step list from NAVIS

    @property
    def active(self) -> bool:
        return self._active

    @property
    def armed(self) -> bool:
        return self._armed

    def arm(self, plan_steps: list = None, freeze_callback=None) -> None:
        """Arm TEMPEST at the start of a TRITON execution session."""
        self._armed        = True
        self._active       = True
        self._step_times   = []
        self._step_log     = []
        self._retry_counts = {}
        self._freeze_fn    = freeze_callback
        self._plan_steps   = plan_steps or []

    def disarm(self) -> None:
        """Disarm at end of session — TRITON completed or was cancelled."""
        self._armed  = False
        self._active = False

    def record_step(self, command: str, asset_id: str, result: dict) -> dict:
        """
        Record a TRITON execution step and check all tempo rules.
        Returns assessment. Triggers freeze callback if any rule is violated.
        """
        now = time.time()
        step_num = len(self._step_times) + 1
        violations = []

        # Rule 1: too fast
        if self._step_times:
            gap = now - self._step_times[-1]
            if gap < MIN_INTER_STEP_SECONDS:
                violations.append(
                    f"Step {step_num} too fast — {gap:.2f}s since last step (min: {MIN_INTER_STEP_SECONDS}s)"
                )

        # Rule 2: too many steps
        if step_num > MAX_STEPS_PER_SESSION:
            violations.append(
                f"Session step count {step_num} exceeds maximum {MAX_STEPS_PER_SESSION}"
            )

        # Rule 3: retry exceeded
        self._retry_counts[command] = self._retry_counts.get(command, 0) + 1
        if self._retry_counts[command] > MAX_RETRIES_PER_STEP:
            violations.append(
                f"Command {command} retried {self._retry_counts[command]} times (max: {MAX_RETRIES_PER_STEP})"
            )

        # Rule 4: command not in approved plan
        if self._plan_steps:
            approved_commands = {s["command"] for s in self._plan_steps}
            if command not in approved_commands:
                violations.append(
                    f"Command {command} is not in the approved NAVIS plan"
                )

        self._step_times.append(now)

        tempo_ok = len(violations) == 0
        assessment = {
            "step_num":     step_num,
            "command":      command,
            "asset_id":     asset_id,
            "tempo_ok":     tempo_ok,
            "violations":   violations,
            "freeze_issued":False,
            "monitored_by": self.NAME,
            "timestamp":    datetime.now().isoformat(),
        }

        # Trigger freeze if tempo violated
        if violations and self._freeze_fn:
            assessment["freeze_issued"] = True
            self._freeze_fn(f"TEMPEST freeze — {'; '.join(violations)}")

        # Enhance tempo assessment with BlueVerse
        if _BV_OK and _get_bv_client:
            try:
                status = "OK" if tempo_ok else f"VIOLATED — {'; '.join(violations)}"
                message = (
                    f"TEMPEST tempo check step {step_num}: {command} on {asset_id}. "
                    f"Tempo status: {status}. "
                    f"In 1 sentence, report this tempo monitoring result."
                )
                bv_msg = _get_bv_client().invoke_safe("TEMPEST", message, fallback="")
                if bv_msg:
                    assessment["bv_message"] = bv_msg
            except Exception:
                pass

        self._step_log.append(assessment)
        return assessment

    def reset(self):
        self._armed        = False
        self._active       = False
        self._step_times   = []
        self._step_log     = []
        self._retry_counts = {}
        self._freeze_fn    = None
        self._plan_steps   = []

    def status(self) -> dict:
        return {
            "name":           self.NAME,
            "zone":           self.ZONE,
            "role":           self.ROLE,
            "description":    self.DESCRIPTION,
            "active":         self._active,
            "armed":          self._armed,
            "steps_recorded": len(self._step_times),
            "step_log":       self._step_log[-5:],
        }
