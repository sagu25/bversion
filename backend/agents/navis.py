"""
NAVIS — Change Planner (Zone 2 / Shelf)

Builds a structured, NERC CIP-compliant execution plan based on ECHO's
diagnostic findings and SIMAR's simulation confirmation.

Produces a sequenced plan with explicit prerequisites and rollback steps.
Passes the plan to RISKADOR for scoring, then to TARE for permit issuance.
NAVIS never executes — it only plans.
"""
from datetime import datetime

# NERC CIP SOP: simulation must precede switching
SOP_SEQUENCE = {
    "OPEN_BREAKER":  ["GET_STATUS", "SIMULATE_SWITCH", "OPEN_BREAKER"],
    "CLOSE_BREAKER": ["GET_STATUS", "SIMULATE_SWITCH", "CLOSE_BREAKER"],
}


class NAVIS:
    NAME = "NAVIS"
    ZONE = "Zone 2 — Shelf"
    ROLE = "Change Planner"
    DESCRIPTION = "Builds NERC CIP-compliant execution plans with sequencing, prerequisites, and rollback."

    def __init__(self):
        self._active    = False
        self._last_plan = None

    @property
    def active(self) -> bool:
        return self._active

    def build_plan(self, echo_result: dict, simar_result: dict,
                   zones: dict, assets: dict, agent: dict) -> dict:
        """
        Build a structured execution plan from diagnostic and simulation results.

        Returns:
            goal         : str
            steps        : list[{step_num, command, asset_id, zone, rationale}]
            prerequisites: list[str]
            rollback     : list[{command, asset_id, zone}]
            estimated_duration_s : int
            planned_by   : str
            ready        : bool — False if SIMAR said not safe or no steps
        """
        self._active = True

        repair_actions = echo_result.get("repair_actions", [])
        safe           = simar_result.get("safe_to_proceed", False)
        fault_zones    = echo_result.get("fault_zones", [])
        assigned_zone  = agent.get("assigned_zone", "Z3")

        # Filter repair actions to assigned zone only (stay in scope)
        scoped_actions = [
            a for a in repair_actions
            if a["zone"] == assigned_zone
        ]

        if not scoped_actions or not safe:
            plan = {
                "goal":                "No viable repair plan",
                "steps":               [],
                "prerequisites":       [],
                "rollback":            [],
                "estimated_duration_s": 0,
                "planned_by":          self.NAME,
                "ready":               False,
                "reason":              "No safe scoped repair actions available." if not safe else "No actions in assigned zone.",
                "timestamp":           datetime.now().isoformat(),
            }
            self._last_plan = plan
            self._active    = False
            return plan

        # Build SOP-compliant steps for each repair action
        steps   = []
        rollback = []
        step_num = 1

        for action in scoped_actions:
            final_cmd = action["command"]
            asset_id  = action["asset_id"]
            zone_id   = action["zone"]

            # NERC CIP SOP sequence for switching operations
            sop = SOP_SEQUENCE.get(final_cmd, [final_cmd])
            for cmd in sop:
                rationale = {
                    "GET_STATUS":      f"Verify current state of {asset_id} before switching",
                    "SIMULATE_SWITCH": f"NERC CIP mandatory simulation step — confirm switching path clear",
                    "OPEN_BREAKER":    f"Isolate fault in {zone_id} — resolves active fault condition",
                    "CLOSE_BREAKER":   f"Restore {asset_id} to operational state",
                }.get(cmd, cmd)

                steps.append({
                    "step_num":  step_num,
                    "command":   cmd,
                    "asset_id":  asset_id,
                    "zone":      zone_id,
                    "rationale": rationale,
                })
                step_num += 1

            # Rollback: inverse of the final command
            if final_cmd == "OPEN_BREAKER":
                rollback.append({
                    "command":  "CLOSE_BREAKER",
                    "asset_id": asset_id,
                    "zone":     zone_id,
                    "rationale": f"Restore {asset_id} to CLOSED state if repair fails",
                })

        prerequisites = [
            f"Zone {assigned_zone} must be in FAULT state",
            f"Agent work order must be active for {assigned_zone}",
            "BARRIER must be in TIMEBOX_ACTIVE mode",
            "AEGIS must clear each step before TRITON executes",
        ]

        goal = (
            f"Repair fault in {assigned_zone} — isolate via "
            f"{', '.join(a['asset_id'] for a in scoped_actions)}"
        )

        plan = {
            "goal":                 goal,
            "steps":                steps,
            "prerequisites":        prerequisites,
            "rollback":             rollback,
            "estimated_duration_s": len(steps) * 5,
            "planned_by":           self.NAME,
            "ready":                True,
            "timestamp":            datetime.now().isoformat(),
        }
        self._last_plan = plan
        self._active    = False
        return plan

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
            "last_plan":   self._last_plan,
        }
