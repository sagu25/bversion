"""
TRITON — Execution Agent (Zone 1 / Trench)

Executes only explicitly approved, time-boxed actions within strict scope.
Never self-authorizes. Every execution step must pass AEGIS validation first.

Flow per step:
  TARE issues permit → AEGIS validates → TRITON executes → TEMPEST records

If AEGIS vetoes a step, TRITON stops immediately.
If TEMPEST detects a tempo violation, the freeze_fn fires and TRITON stops.
TRITON calls execute_fn (tare_engine.process_command) for real grid effect.
"""
from datetime import datetime


class TRITON:
    NAME = "TRITON"
    ZONE = "Zone 1 — Trench"
    ROLE = "Execution Agent"
    DESCRIPTION = "Executes TARE-approved, time-boxed steps only. Stopped immediately by AEGIS veto."

    def __init__(self):
        self._active         = False
        self._permit         = None
        self._execute_fn     = None   # callback: process_command(cmd, asset, zone)
        self._execution_log  = []
        self._stopped        = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def has_permit(self) -> bool:
        return self._permit is not None

    def arm(self, execute_fn, permit: dict) -> None:
        """
        TARE arms TRITON with an execute callback and a time-boxed permit.
        execute_fn: tare_engine.process_command(command, asset_id, zone)
        permit: {scope, allowed_commands, issued_at, issued_by}
        """
        self._execute_fn    = execute_fn
        self._permit        = permit
        self._execution_log = []
        self._stopped       = False

    def revoke(self) -> None:
        """TARE or TEMPEST revokes the permit — TRITON stops immediately."""
        self._permit  = None
        self._stopped = True
        self._active  = False

    def execute_step(self, command: str, asset_id: str, zone: str) -> dict:
        """
        Execute one approved step via the engine callback.
        Returns the execution result.
        Blocked if: no permit, stopped flag set, or command not in allowed list.
        """
        if self._stopped or not self._permit:
            return {
                "status":   "BLOCKED",
                "reason":   "No active permit or TRITON was stopped",
                "command":  command,
                "asset_id": asset_id,
                "zone":     zone,
            }

        allowed = self._permit.get("allowed_commands", [])
        if allowed and command not in allowed:
            return {
                "status":   "BLOCKED",
                "reason":   f"{command} not in permit scope {allowed}",
                "command":  command,
                "asset_id": asset_id,
                "zone":     zone,
            }

        self._active = True
        try:
            result = self._execute_fn(command, asset_id, zone)
            entry = {
                "command":     command,
                "asset_id":    asset_id,
                "zone":        zone,
                "decision":    result.get("decision"),
                "reason":      result.get("reason"),
                "status":      "EXECUTED",
                "executed_by": self.NAME,
                "timestamp":   datetime.now().isoformat(),
            }
        except Exception as e:
            entry = {
                "command":     command,
                "asset_id":    asset_id,
                "zone":        zone,
                "status":      "ERROR",
                "error":       str(e),
                "executed_by": self.NAME,
                "timestamp":   datetime.now().isoformat(),
            }
        finally:
            self._active = False

        self._execution_log.append(entry)
        return entry

    def reset(self):
        self._active        = False
        self._permit        = None
        self._execute_fn    = None
        self._execution_log = []
        self._stopped       = False

    def status(self) -> dict:
        return {
            "name":          self.NAME,
            "zone":          self.ZONE,
            "role":          self.ROLE,
            "description":   self.DESCRIPTION,
            "active":        self._active,
            "has_permit":    self.has_permit,
            "stopped":       self._stopped,
            "steps_executed":len(self._execution_log),
            "execution_log": self._execution_log[-5:],
        }
