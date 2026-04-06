"""
RISKADOR — Risk Scoring Agent (Zone 2 / Shelf)

Evaluates proposed NAVIS plans across four risk dimensions:
  - Blast Radius   : how many assets and zones are affected
  - Reversibility  : can the actions be undone if something goes wrong
  - Urgency        : how time-critical is the situation
  - Confidence     : how certain is the ECHO diagnostic

Returns a composite 0–100 score and a recommendation: PROCEED / CAUTION / HOLD.
Wakes after NAVIS produces a plan. Sleeps immediately after scoring.
"""
from datetime import datetime


class RISKADOR:
    NAME = "RISKADOR"
    ZONE = "Zone 2 — Shelf"
    ROLE = "Risk Scoring Agent"
    DESCRIPTION = "Scores plans for blast radius, reversibility, urgency, and confidence."

    # Reversible commands — can be undone with the inverse
    REVERSIBLE = {
        "OPEN_BREAKER":  "CLOSE_BREAKER",
        "CLOSE_BREAKER": "OPEN_BREAKER",
        "GET_STATUS":    None,
        "SIMULATE_SWITCH": None,
    }
    IRREVERSIBLE = {"RESTART_CONTROLLER"}

    def __init__(self):
        self._active     = False
        self._last_score = None

    @property
    def active(self) -> bool:
        return self._active

    def score(self, plan: dict, zones: dict = None, assets: dict = None,
              echo_result: dict = None) -> dict:
        """
        Score a NAVIS plan across 4 risk dimensions.

        Returns:
            composite_score  : int 0–100 (lower = safer)
            dimensions       : dict with per-dimension scores
            recommendation   : "PROCEED" | "CAUTION" | "HOLD"
            rationale        : str — plain English explanation
            scored_by        : str
        """
        self._active = True
        zones  = zones  or {}
        assets = assets or {}

        steps = plan.get("steps", [])
        rollback = plan.get("rollback", [])

        # ── Dimension 1: Blast Radius (0=minimal, 100=wide) ────────────────
        affected_assets = {s["asset_id"] for s in steps if s["command"] not in ("GET_STATUS", "SIMULATE_SWITCH")}
        affected_zones  = {s["zone"]     for s in steps if s["command"] not in ("GET_STATUS", "SIMULATE_SWITCH")}
        blast_score = min(100, len(affected_assets) * 20 + len(affected_zones) * 15)

        # ── Dimension 2: Reversibility (0=fully reversible, 100=irreversible) ──
        irreversible_steps = [s for s in steps if s["command"] in self.IRREVERSIBLE]
        has_rollback = len(rollback) > 0
        if irreversible_steps:
            rev_score = 80
        elif not has_rollback:
            rev_score = 40
        else:
            rev_score = 10   # rollback plan exists, commands are reversible

        # ── Dimension 3: Urgency (0=low urgency, 100=critical) ─────────────
        fault_zones = [zid for zid, z in zones.items() if z.get("health") == "FAULT"]
        if len(fault_zones) >= 2:
            urgency_score = 90
        elif len(fault_zones) == 1:
            urgency_score = 70
        else:
            urgency_score = 20   # no active fault — why are we executing?

        # ── Dimension 4: Confidence (0=uncertain, 100=confirmed) ───────────
        if echo_result and echo_result.get("confirmed"):
            confidence_score = 90
        elif echo_result:
            confidence_score = 40
        else:
            confidence_score = 20

        # ── Composite (weighted) ───────────────────────────────────────────
        # Risk = blast + reversibility weighted down by confidence + urgency modifier
        # High urgency REDUCES risk threshold (we accept more risk to fix a fault faster)
        raw = (blast_score * 0.35) + (rev_score * 0.40) + ((100 - confidence_score) * 0.25)
        urgency_modifier = -10 if urgency_score >= 70 else 0   # fault active → accept risk
        composite = max(0, min(100, int(raw + urgency_modifier)))

        # ── Recommendation ─────────────────────────────────────────────────
        if composite < 35:
            recommendation = "PROCEED"
            rec_color = "green"
        elif composite < 60:
            recommendation = "CAUTION"
            rec_color = "amber"
        else:
            recommendation = "HOLD"
            rec_color = "red"

        rationale = (
            f"Blast radius: {len(affected_assets)} asset(s), {len(affected_zones)} zone(s) — score {blast_score}. "
            f"Reversibility: {'irreversible steps present' if irreversible_steps else 'rollback plan available' if has_rollback else 'no rollback plan'} — score {rev_score}. "
            f"Urgency: {len(fault_zones)} active fault zone(s) — score {urgency_score}. "
            f"Confidence: {'ECHO confirmed' if echo_result and echo_result.get('confirmed') else 'unconfirmed'} — score {confidence_score}. "
            f"Composite risk: {composite}/100 → {recommendation}."
        )

        result = {
            "plan_goal":       plan.get("goal", "unknown"),
            "composite_score": composite,
            "dimensions": {
                "blast_radius":   blast_score,
                "reversibility":  rev_score,
                "urgency":        urgency_score,
                "confidence":     confidence_score,
            },
            "recommendation":  recommendation,
            "rec_color":       rec_color,
            "rationale":       rationale,
            "scored_by":       self.NAME,
            "timestamp":       datetime.now().isoformat(),
        }
        self._last_score = result
        self._active     = False
        return result

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
            "last_score":  self._last_score,
        }
