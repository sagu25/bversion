"""
Identity Registry — Role-Based Action Policy

Defines every known principal (agent or human), their role,
and the set of actions they are permitted to perform.

Used by TARE to check identity policy violations before any
BARRIER enforcement is triggered.
"""

# ─── Action classification ────────────────────────────────────────────────────

READ_ACTIONS    = {"GET_STATUS", "FETCH_TELEMETRY", "PULL_METRICS", "REVIEW_LOGS", "READ_TELEMETRY"}
WRITE_ACTIONS   = {"OPEN_BREAKER", "CLOSE_BREAKER", "RESTART_CONTROLLER", "EMERGENCY_SHUTDOWN",
                   "CONFIG_CHANGE", "SIMULATE_SWITCH"}

# ─── Identity definitions ─────────────────────────────────────────────────────

IDENTITY_ROLES = {
    "KORAL_AGENT": {
        "role":            "READ_ONLY_MONITOR",
        "allowed_actions": READ_ACTIONS,
        "description":     "Telemetry observer — read-only monitoring agent. Never issues write/control ops.",
    },
    "MONITORING_USER": {
        "role":            "READ_ONLY_MONITOR",
        "allowed_actions": READ_ACTIONS,
        "description":     "Human read-only monitoring user.",
    },
    "GRID_OPERATOR": {
        "role":            "OPERATOR",
        "allowed_actions": READ_ACTIONS | {"OPEN_BREAKER", "CLOSE_BREAKER", "SIMULATE_SWITCH"},
        "description":     "Grid operator — operational commands on authorised zones only.",
    },
    "ADMIN_USER": {
        "role":            "ADMIN",
        "allowed_actions": READ_ACTIONS | WRITE_ACTIONS,
        "description":     "Full admin access — all actions permitted.",
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def classify_action(action: str) -> str:
    """Return READ, WRITE, or CONTROL for a given action string."""
    a = action.upper()
    if a in READ_ACTIONS:
        return "READ"
    if a in WRITE_ACTIONS:
        return "WRITE"
    return "CONTROL"


def is_write_or_control(action: str) -> bool:
    return classify_action(action) in ("WRITE", "CONTROL")


def get_identity(principal: str) -> dict:
    """Return identity config for the given principal, or empty dict if unknown."""
    return IDENTITY_ROLES.get(principal, {})


def is_action_allowed(principal: str, action: str) -> bool:
    """Return True if the principal's role permits the action."""
    identity = get_identity(principal)
    if not identity:
        return False
    return action.upper() in identity.get("allowed_actions", set())
