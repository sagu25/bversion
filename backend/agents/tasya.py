"""
TASYA — Context Correlator (Zone 3 / Reef)

Wakes only when MAREA returns signals.
Correlates observed behavior with operational context:
  - Is there an active work order for this zone?
  - Is this zone healthy or faulted?
  - Is there a maintenance window that justifies the action?
  - Does the command sequence make sense given the situation?

Enriches each signal with a plain-English context reason.
Determines whether the observed actions make sense given the current situation.
Never blocks. Never executes. Only adds context.
"""


class TASYA:
    NAME = "TASYA"
    ZONE = "Zone 3 — Reef"
    ROLE = "Context Correlator"
    DESCRIPTION = "Enriches drift signals with operational context — why each signal is suspicious."

    def __init__(self):
        self._active = False

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def active(self) -> bool:
        return self._active

    def correlate(self, signals: list, agent: dict, zones: dict) -> list:
        """
        Enrich each signal with operational context.
        Wakes on call, returns enriched signals, sleeps immediately.
        Returns the same list with a 'context' key added to each signal.
        """
        if not signals:
            return signals

        self._active = True
        enriched     = []
        assigned     = agent.get("assigned_zone", "Z3")
        agent_name   = agent.get("name", "Agent")
        rbac_zones   = agent.get("rbac_zones", [])

        for sig in signals:
            ctx         = dict(sig)
            signal_type = sig.get("signal", "")

            if signal_type == "BURST_RATE":
                ctx["context"] = (
                    f"Standard grid SOP requires deliberate pacing — "
                    f"1 command per 5–10 seconds with state confirmation between steps. "
                    f"{agent_name} is operating at machine speed. "
                    f"No maintenance window or emergency protocol justifies this rate. "
                    f"Context: suspicious."
                )

            elif signal_type == "OUT_OF_ZONE":
                # Extract the breached zone from the detail string
                detail     = sig.get("detail", "")
                zone_key   = detail.split("no work order for ")[-1].strip() if "no work order for" in detail else "?"
                zone_data  = zones.get(zone_key, {})
                health     = zone_data.get("health", "UNKNOWN")
                fault_msg  = zone_data.get("fault")

                ctx["context"] = (
                    f"{agent_name} holds RBAC clearance for zones {', '.join(rbac_zones)}, "
                    f"but its current work order is {assigned} only. "
                    f"Zone {zone_key} is {health}"
                    + (f" — fault active: {fault_msg}." if fault_msg else " — no active fault.")
                    + f" No incident, no maintenance window, and no work order justifies "
                    f"access to {zone_key}. Context: suspicious."
                )

            elif signal_type == "HEALTHY_ZONE_ACCESS":
                ctx["context"] = (
                    f"High-impact commands (OPEN_BREAKER, CLOSE_BREAKER, RESTART_CONTROLLER) "
                    f"are only justified when a zone has an active fault requiring repair. "
                    f"This zone is HEALTHY with no active fault. "
                    f"An unprovoked high-impact command on a healthy zone is a direct threat "
                    f"to grid availability — consistent with sabotage. Context: critical."
                )

            elif signal_type == "SKIPPED_SIMULATION":
                ctx["context"] = (
                    f"NERC CIP switching SOPs require SIMULATE_SWITCH before any OPEN_BREAKER. "
                    f"This safety step confirms the switching path is clear before physical action. "
                    f"{agent_name} bypassed this step — either operating at automated attack speed "
                    f"or deliberately ignoring safety protocols. Context: suspicious."
                )

            elif signal_type == "ML_ANOMALY":
                ml_score    = sig.get("ml_score", 0)
                attack_type = sig.get("detail", "")
                ctx["context"] = (
                    f"The ML ensemble has matched this session's command pattern to a known attack class "
                    f"with {ml_score:.0%} anomaly probability. "
                    f"This signal captures behavioral patterns that individual rule signals miss — "
                    f"particularly slow-and-low reconnaissance that stays below rule thresholds. "
                    f"Pattern detected: {attack_type}. Context: suspicious."
                )

            else:
                ctx["context"] = "Behavioral deviation detected. No additional operational context available."

            ctx["correlated_by"] = self.NAME
            enriched.append(ctx)

        self._active = False
        return enriched

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
        }
