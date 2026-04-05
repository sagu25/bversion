"""
TARE Multi-Agent System — All 12 Zone Agents + BARRIER

Zone 3 — Reef (Observe & Recommend) — IMPLEMENTED:
    KORAL   — Telemetry Observer
    MAREA   — Drift Analyst
    TASYA   — Context Correlator
    NEREUS  — Recommendation Agent

Zone 2 — Shelf (Diagnose & Prepare) — STUB (Phase 2):
    ECHO    — Diagnostics Agent
    SIMAR   — Simulation & What-If Agent
    NAVIS   — Change Planner
    RISKADOR— Risk Scoring Agent

Zone 1 — Trench (Execute with Safety) — STUB (Phase 2):
    TRITON  — Execution Agent
    AEGIS   — Safety Validator
    TEMPEST — Session & Tempo Monitor
    LEVIER  — Rollback & Recovery Agent

Zone 4 — Policy Enforcement — IMPLEMENTED:
    BARRIER — Gateway Policy Enforcer (sole ALLOW/DENY authority)

Total: 12 zone agents + BARRIER
"""

# Zone 3 — Reef (implemented)
from .koral    import KORAL
from .marea    import MAREA
from .tasya    import TASYA
from .nereus   import NEREUS

# Zone 2 — Shelf (stubs)
from .echo     import ECHO
from .simar    import SIMAR
from .navis    import NAVIS
from .riskador import RISKADOR

# Zone 1 — Trench (stubs)
from .triton      import TRITON
from .aegis_agent import AEGIS
from .tempest     import TEMPEST
from .levier      import LEVIER

# Zone 4 — Policy Enforcement (implemented)
from .barrier  import BARRIER

__all__ = [
    # Zone 3
    "KORAL", "MAREA", "TASYA", "NEREUS",
    # Zone 2
    "ECHO", "SIMAR", "NAVIS", "RISKADOR",
    # Zone 1
    "TRITON", "AEGIS", "TEMPEST", "LEVIER",
    # Zone 4
    "BARRIER",
]
