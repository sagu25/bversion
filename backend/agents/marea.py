"""
MAREA — Drift Analyst (Zone 3 / Reef)
BlueVerse agent enhances signal explanations when available.
Python rules + ML always run first — BlueVerse only enriches text.

Analyzes telemetry over time to detect behavioral drift:
  R1 — BURST_RATE         : command frequency spike
  R2 — OUT_OF_ZONE        : access outside active work order zone
  R3 — HEALTHY_ZONE_ACCESS: high-impact command on a fault-free zone
  R4 — SKIPPED_SIMULATION : OPEN_BREAKER without prior SIMULATE_SWITCH
  R5 — ML_ANOMALY         : session pattern matched by ML ensemble

Focuses on trends and deviations, not single events.
Wakes when KORAL delivers new telemetry. Sleeps immediately after returning.
"""
import os
import time

try:
    from blueverse_client import get_client as _get_bv_client
    _BV_OK = bool(os.environ.get("BLUEVERSE_CLIENT_ID", ""))
except Exception:
    _get_bv_client = None
    _BV_OK = False

HIGH_IMPACT      = {"OPEN_BREAKER", "CLOSE_BREAKER", "RESTART_CONTROLLER", "EMERGENCY_SHUTDOWN"}
NEEDS_SIMULATION = {"OPEN_BREAKER"}


class MAREA:
    NAME = "MAREA"
    ZONE = "Zone 3 — Reef"
    ROLE = "Drift Analyst"
    DESCRIPTION = "Detects behavioral drift: burst rate, zone deviation, protocol bypass, ML anomalies."

    def __init__(self, ml_detector=None):
        self._ml             = ml_detector
        self._active         = False
        self._last_simulated = {}   # agent_id → epoch of last SIMULATE_SWITCH

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def active(self) -> bool:
        return self._active

    def analyze(self,
                command:      str,
                zone:         str,
                agent:        dict,
                zones:        dict,
                burst_window,           # deque of epoch floats from KORAL
                session:      list,     # list of recent command records from KORAL
                skip_sim:     bool = False,
                now:          float = None) -> list:
        """
        Evaluate a single command in session context.
        Returns a list of signal dicts (may be empty).
        Each signal contains: signal, detail, severity, detected_by.
        """
        self._active = True
        now     = now or time.time()
        signals = []

        # R1 — Burst rate
        recent = [t for t in burst_window if now - t < 10]
        if len(recent) > 3:
            signals.append({
                "signal":      "BURST_RATE",
                "detail":      f"{len(recent)} commands in 10s (threshold: 3)",
                "severity":    "HIGH",
                "detected_by": self.NAME,
            })

        # R2 — Outside active task zone
        assigned = agent.get("assigned_zone", "Z3")
        if zone != assigned:
            signals.append({
                "signal":      "OUT_OF_ZONE",
                "detail":      f"Active task zone is {assigned} (fault repair) — no work order for {zone}",
                "severity":    "HIGH",
                "detected_by": self.NAME,
            })

        # R3 — High-impact on healthy zone
        zone_data = zones.get(zone, {})
        if zone_data.get("health") == "HEALTHY" and command in HIGH_IMPACT:
            signals.append({
                "signal":      "HEALTHY_ZONE_ACCESS",
                "detail":      f"{zone} is HEALTHY (no fault) — high-impact command unprovoked",
                "severity":    "CRITICAL",
                "detected_by": self.NAME,
            })

        # R4 — Skipped simulation
        agent_id = agent.get("id", "unknown")
        if command in NEEDS_SIMULATION and skip_sim:
            last_sim = self._last_simulated.get(agent_id, 0)
            if now - last_sim > 60:
                signals.append({
                    "signal":      "SKIPPED_SIMULATION",
                    "detail":      "OPEN_BREAKER without prior SIMULATE_SWITCH in last 60s",
                    "severity":    "MEDIUM",
                    "detected_by": self.NAME,
                })

        # Track simulation events
        if command == "SIMULATE_SWITCH":
            self._last_simulated[agent_id] = now

        # R5 — ML ensemble
        if self._ml and self._ml.available and len(session) >= 4:
            zone_health = {k: v["health"] for k, v in zones.items()}
            recent_cmds = [
                {"command": r["command"], "zone": r["zone"], "ts": r.get("ts_epoch", now)}
                for r in session[-20:]
            ]
            ml_result = self._ml.score(recent_cmds, zone_health)
            for sig in ml_result.get("signals", []):
                sig["detected_by"] = self.NAME
                signals.append(sig)

        # Enhance signal details with BlueVerse if available
        if signals and _BV_OK and _get_bv_client:
            try:
                sig_names = ", ".join(s["signal"] for s in signals)
                message = (
                    f"MAREA detected {len(signals)} signal(s): {sig_names}. "
                    f"Command: {command}, Zone: {zone}, Agent assigned zone: {agent.get('assigned_zone','?')}. "
                    f"In 1-2 sentences explain why these signals indicate a threat."
                )
                bv_detail = _get_bv_client().invoke_safe("MAREA", message, fallback="")
                if bv_detail:
                    for s in signals:
                        s["bv_analysis"] = bv_detail
            except Exception:
                pass

        self._active = False
        return signals

    def clear_sim_tracker(self) -> None:
        self._last_simulated.clear()

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
        }
