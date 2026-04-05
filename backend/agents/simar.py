"""
SIMAR — Simulation & What-If Agent (Zone 2 / Shelf)

Simulates proposed repair actions against a copy of the live OT state.
Answers: "What would happen if we execute this plan?" without touching
any real asset.

Wakes after ECHO confirms the diagnostic. Takes ECHO's proposed repair
actions, applies them to a frozen snapshot of zones and assets, and
returns the predicted outcome including state changes and risk indicators.
"""
import copy
from datetime import datetime

HIGH_IMPACT = {"OPEN_BREAKER", "CLOSE_BREAKER", "RESTART_CONTROLLER"}


class SIMAR:
    NAME = "SIMAR"
    ZONE = "Zone 2 — Shelf"
    ROLE = "Simulation & What-If Agent"
    DESCRIPTION = "Simulates proposed changes and predicts their impact without touching live systems."

    def __init__(self):
        self._active      = False
        self._last_result = None

    @property
    def active(self) -> bool:
        return self._active

    def simulate(self, proposed_steps: list, zones: dict, assets: dict) -> dict:
        """
        Run a what-if simulation on proposed steps.

        proposed_steps: list of {command, asset_id, zone}
        zones:  current live zone states (read-only — deep copied internally)
        assets: current live asset states (read-only — deep copied internally)

        Returns:
            safe_to_proceed    : bool
            predicted_zones    : dict — zone states after simulation
            predicted_assets   : dict — asset states after simulation
            affected_assets    : list — which assets change state
            affected_zones     : list — which zones change health
            risk_indicators    : list — anything flagged during simulation
            summary            : str — human-readable outcome
            simulated_by       : str
        """
        self._active = True

        # Deep copy — never touch live state
        sim_zones  = copy.deepcopy(zones)
        sim_assets = copy.deepcopy(assets)

        affected_assets = []
        affected_zones  = []
        risk_indicators = []

        for step in proposed_steps:
            cmd      = step.get("command")
            asset_id = step.get("asset_id")
            zone_id  = step.get("zone")

            asset = sim_assets.get(asset_id)
            zone  = sim_zones.get(zone_id)

            if not asset or not zone:
                risk_indicators.append(
                    f"Unknown asset {asset_id} or zone {zone_id} — cannot simulate step."
                )
                continue

            # Simulate state change
            prev_asset_state = asset["state"]
            prev_zone_health = zone["health"]

            if cmd == "OPEN_BREAKER":
                asset["state"] = "OPEN"
                # If zone was FAULT, fault is resolved by isolation
                if zone["health"] == "FAULT":
                    zone["health"] = "HEALTHY"
                    zone["fault"]  = None
                    zone["color"]  = "green"
                    affected_zones.append(f"{zone_id}: FAULT → HEALTHY")
                elif zone["health"] == "HEALTHY":
                    risk_indicators.append(
                        f"Opening breaker {asset_id} in HEALTHY zone {zone_id} — "
                        f"unnecessary action, may cause outage."
                    )
                affected_assets.append(
                    f"{asset_id}: {prev_asset_state} → OPEN"
                )

            elif cmd == "CLOSE_BREAKER":
                asset["state"] = "CLOSED"
                affected_assets.append(f"{asset_id}: {prev_asset_state} → CLOSED")

            elif cmd == "RESTART_CONTROLLER":
                asset["state"] = "RESTARTING"
                risk_indicators.append(
                    f"RESTART_CONTROLLER on {asset_id} — disruptive, takes 30–90s to recover."
                )
                affected_assets.append(f"{asset_id}: {prev_asset_state} → RESTARTING")

            elif cmd in ("GET_STATUS", "SIMULATE_SWITCH"):
                # Read-only / diagnostic — no state change
                pass

        # Determine if safe to proceed
        critical_risks = [r for r in risk_indicators if "outage" in r or "RESTART" in r]
        safe_to_proceed = len(critical_risks) == 0

        summary = (
            f"Simulation complete. {len(proposed_steps)} step(s) simulated. "
            + (f"Asset changes: {', '.join(affected_assets)}. " if affected_assets else "No asset state changes. ")
            + (f"Zone changes: {', '.join(affected_zones)}. " if affected_zones else "No zone health changes. ")
            + (f"Risk indicators: {len(risk_indicators)}. " if risk_indicators else "No risk indicators. ")
            + ("Safe to proceed." if safe_to_proceed else "Risks detected — review required.")
        )

        result = {
            "safe_to_proceed":  safe_to_proceed,
            "predicted_zones":  sim_zones,
            "predicted_assets": sim_assets,
            "affected_assets":  affected_assets,
            "affected_zones":   affected_zones,
            "risk_indicators":  risk_indicators,
            "summary":          summary,
            "simulated_by":     self.NAME,
            "timestamp":        datetime.now().isoformat(),
        }
        self._last_result = result
        self._active      = False
        return result

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
            "last_result": self._last_result,
        }
