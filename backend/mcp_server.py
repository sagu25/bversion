"""
AEGIS-ID MCP Server
Exposes all 13 TARE agents as MCP tools over plain HTTP (JSON-RPC 2.0).

BlueVerse registration:
    Type : MCP Remote - HTTP
    URL  : https://<ngrok-url>/mcp

Supported JSON-RPC methods:
    initialize          → handshake
    notifications/initialized → ack (no response)
    tools/list          → all AEGIS tool definitions
    tools/call          → execute a tool against the live TARE engine

Tools per zone:
    Zone 3 — Reef    : tare_evaluate_command, tare_get_status,
                       tare_get_audit_log, barrier_get_policy,
                       koral_get_session, marea_get_signals,
                       nereus_get_recommendation
    Zone 2 — Shelf   : echo_diagnose, simar_simulate,
                       navis_build_plan, riskador_score_plan
    Zone 1 — Trench  : triton_get_status
    All zones        : tare_get_all_agents_status,
                       tare_approve_timebox, tare_deny_timebox, tare_reset
"""
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# ─── Tool Definitions ─────────────────────────────────────────────────────────

TOOLS = [

    # ── Zone 3 — Reef ─────────────────────────────────────────────────────────

    {
        "name": "tare_evaluate_command",
        "description": (
            "Submit a command through the full TARE security pipeline. "
            "KORAL observes → BARRIER enforces → MAREA analyzes for drift signals → "
            "TASYA correlates context → NEREUS recommends action to TARE. "
            "Returns ALLOW/DENY decision, all signals detected, and current TARE mode."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command":  {"type": "string",
                             "description": "Command to evaluate: OPEN_BREAKER, CLOSE_BREAKER, GET_STATUS, SIMULATE_SWITCH, RESTART_CONTROLLER, EMERGENCY_SHUTDOWN"},
                "asset_id": {"type": "string",
                             "description": "Target asset ID e.g. BRK-301, FDR-205, BRK-110"},
                "zone":     {"type": "string",
                             "description": "Zone where command is issued: Z1, Z2, or Z3"},
            },
            "required": ["command", "asset_id", "zone"],
        },
    },

    {
        "name": "tare_get_status",
        "description": (
            "Get full TARE system status: active enforcement mode "
            "(NORMAL / FREEZE / DOWNGRADE / TIMEBOX_ACTIVE / SAFE), "
            "command stats, zone health, agent identity, "
            "and active ServiceNow incident if any."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "tare_get_audit_log",
        "description": (
            "Retrieve the gateway audit log — every command processed this session "
            "with its ALLOW/DENY decision, drift signals fired, reason, policy ID, "
            "zone, asset, and timestamp."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "last_n": {"type": "integer",
                           "description": "Number of most recent entries to return (default 20, max 100)"},
            },
            "required": [],
        },
    },

    {
        "name": "barrier_get_policy",
        "description": (
            "Get BARRIER's current enforcement mode and what each mode means: "
            "NORMAL (standard RBAC), FREEZE (all high-impact ops blocked), "
            "DOWNGRADE (diagnostics only), TIMEBOX_ACTIVE (supervisor window open), "
            "SAFE (read-only)."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "koral_get_session",
        "description": (
            "Ask KORAL for the raw telemetry session log — "
            "the last N command records it has observed this session, "
            "including timestamps, zones, and asset IDs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "last_n": {"type": "integer",
                           "description": "Number of session records to return (default 20)"},
            },
            "required": [],
        },
    },

    {
        "name": "marea_get_signals",
        "description": (
            "Ask MAREA for the drift signals it has detected this session. "
            "Returns all anomaly signals: BURST_RATE, OUT_OF_ZONE, "
            "HEALTHY_ZONE_ACCESS, SKIPPED_SIMULATION, ML_ANOMALY."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "nereus_get_recommendation",
        "description": (
            "Ask NEREUS for its latest recommendation to TARE. "
            "Returns the action (FREEZE / ALLOW / MONITOR), confidence score, "
            "and the full human-readable briefing it gave the supervisor."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    # ── Zone 2 — Shelf ────────────────────────────────────────────────────────

    {
        "name": "echo_diagnose",
        "description": (
            "Run ECHO diagnostics on the current OT state. "
            "ECHO checks all zones for active faults, identifies target assets "
            "that need repair action, detects blocking conditions, "
            "and returns a confirmed diagnostic report."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "simar_simulate",
        "description": (
            "Run SIMAR's what-if simulation on proposed repair steps. "
            "SIMAR applies actions to a copy of live OT state and returns "
            "predicted zone/asset changes, risk indicators, and whether it is safe to proceed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "description": "Proposed steps to simulate",
                    "items": {
                        "type": "object",
                        "properties": {
                            "command":  {"type": "string"},
                            "asset_id": {"type": "string"},
                            "zone":     {"type": "string"},
                        },
                        "required": ["command", "asset_id", "zone"],
                    },
                }
            },
            "required": ["steps"],
        },
    },

    {
        "name": "navis_build_plan",
        "description": (
            "Ask NAVIS to build a NERC CIP-compliant execution plan. "
            "NAVIS uses the latest ECHO diagnostic and SIMAR simulation results "
            "to produce a sequenced plan with prerequisites and rollback steps."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "riskador_score_plan",
        "description": (
            "Ask RISKADOR to score the latest NAVIS plan across 4 risk dimensions: "
            "blast radius, reversibility, urgency, and confidence. "
            "Returns a composite 0–100 risk score and a PROCEED / CAUTION / HOLD recommendation."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    # ── Zone 1 — Trench ───────────────────────────────────────────────────────

    {
        "name": "triton_get_status",
        "description": (
            "Get TRITON's current execution status: whether it has an active permit, "
            "how many steps it has executed, and its recent execution log."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    # ── All Zones ─────────────────────────────────────────────────────────────

    {
        "name": "tare_get_all_agents_status",
        "description": (
            "Get the live status of all 13 TARE agents across all four zones: "
            "KORAL, MAREA, TASYA, NEREUS (Zone 3), "
            "ECHO, SIMAR, NAVIS, RISKADOR (Zone 2), "
            "TRITON, AEGIS, TEMPEST, LEVIER (Zone 1), "
            "and BARRIER (Zone 4). Shows which agents are active/sleeping."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "tare_approve_timebox",
        "description": (
            "Approve a supervisor timebox — grants a 3-minute window for high-impact commands "
            "after a FREEZE event. BARRIER mode shifts to TIMEBOX_ACTIVE. "
            "Use only after reviewing NEREUS recommendation and active incident."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "tare_deny_timebox",
        "description": (
            "Deny the timebox request — keeps BARRIER in FREEZE mode. "
            "The active incident remains open and all high-impact operations stay blocked."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    {
        "name": "tare_reset",
        "description": (
            "Reset the full TARE session — clears all gateway logs, signals, incidents, "
            "and returns all zones, assets, and agents to their initial state. "
            "Use only for demo resets or controlled test restarts."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },

    # ── Scenario: Read-Only Write Attempt ─────────────────────────────────────

    {
        "name": "log_identity_action",
        "description": (
            "KORAL logs an identity action attempt — records who (principal) attempted "
            "what action and in which zone. Classifies the action as READ, WRITE, or CONTROL. "
            "Call this before check_identity_policy to build the telemetry trail."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "principal":   {"type": "string",
                                "description": "Identity attempting the action e.g. KORAL_AGENT, MONITORING_USER"},
                "action":      {"type": "string",
                                "description": "Action attempted e.g. OPEN_BREAKER, GET_STATUS, CONFIG_CHANGE"},
                "target_zone": {"type": "string",
                                "description": "Zone where the action was attempted: Z1, Z2, or Z3"},
            },
            "required": ["principal", "action", "target_zone"],
        },
    },

    {
        "name": "check_identity_policy",
        "description": (
            "TARE checks if the principal's registered role permits the attempted action. "
            "If a read-only identity attempts a write/control operation: "
            "KORAL logs it → BARRIER applies READ_ONLY_DOWNGRADE → ServiceNow ticket created. "
            "Returns decision (ALLOW/DENY), violation flag, enforcement details, and incident ID."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "principal":   {"type": "string",
                                "description": "Identity to check e.g. KORAL_AGENT, MONITORING_USER, GRID_OPERATOR"},
                "action":      {"type": "string",
                                "description": "Action the identity is attempting e.g. OPEN_BREAKER, RESTART_CONTROLLER"},
                "target_zone": {"type": "string",
                                "description": "Zone where the action is being attempted: Z1, Z2, or Z3"},
            },
            "required": ["principal", "action", "target_zone"],
        },
    },

    {
        "name": "enforce_readonly_policy",
        "description": (
            "BARRIER directly enforces a READ_ONLY_DOWNGRADE on a principal. "
            "Blocks all write/control actions from that identity going forward. "
            "Use after check_identity_policy confirms a violation, or to manually lock down an identity."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "principal": {"type": "string",
                              "description": "Principal to block e.g. KORAL_AGENT"},
                "action":    {"type": "string",
                              "description": "The write/control action that triggered enforcement"},
            },
            "required": ["principal", "action"],
        },
    },
]


# ─── Tool Executor ────────────────────────────────────────────────────────────

def _execute_tool(name: str, arguments: dict, engine) -> dict:

    # ── tare_evaluate_command ─────────────────────────────────────────────────
    if name == "tare_evaluate_command":
        command  = arguments.get("command", "").upper()
        asset_id = arguments.get("asset_id", "")
        zone     = arguments.get("zone", "").upper()
        if not command or not asset_id or not zone:
            return {"error": "command, asset_id, and zone are all required"}
        engine.process_command(command, asset_id, zone)
        snap = engine._snapshot()
        log  = snap.get("gateway_log", [])
        last = log[-1] if log else {}
        return {
            "command":   command,
            "asset_id":  asset_id,
            "zone":      zone,
            "decision":  last.get("decision", "unknown"),
            "reason":    last.get("reason", ""),
            "policy":    last.get("policy", ""),
            "signals":   last.get("signals", []),
            "tare_mode": snap.get("mode", "NORMAL"),
        }

    # ── tare_get_status ───────────────────────────────────────────────────────
    elif name == "tare_get_status":
        snap  = engine._snapshot()
        stats = snap.get("stats", {})
        zones = snap.get("zones", {})
        agent = snap.get("agent", {})
        inc   = snap.get("active_incident")
        return {
            "tare_mode": snap.get("mode", "NORMAL"),
            "stats": {
                "total":         stats.get("total", 0),
                "allowed":       stats.get("allowed", 0),
                "blocked":       stats.get("denied", 0),
                "freeze_events": stats.get("freeze_events", 0),
            },
            "zones": {
                zid: {"health": z.get("health"), "name": z.get("name"), "fault": z.get("fault")}
                for zid, z in zones.items()
            },
            "agent": {
                "id":         agent.get("id"),
                "name":       agent.get("name"),
                "clearance":  agent.get("clearance"),
                "rbac_zones": agent.get("rbac_zones"),
            },
            "active_incident": {
                "id":          inc.get("incident_id"),
                "priority":    inc.get("priority"),
                "state":       inc.get("state"),
                "assigned_to": inc.get("assigned_to"),
            } if inc else None,
        }

    # ── tare_get_audit_log ────────────────────────────────────────────────────
    elif name == "tare_get_audit_log":
        last_n = min(int(arguments.get("last_n", 20)), 100)
        snap   = engine._snapshot()
        log    = snap.get("gateway_log", [])
        return {"total_entries": len(log), "entries": log[-last_n:]}

    # ── barrier_get_policy ────────────────────────────────────────────────────
    elif name == "barrier_get_policy":
        snap = engine._snapshot()
        mode = snap.get("mode", "NORMAL")
        descriptions = {
            "NORMAL":         "Standard RBAC enforcement. Most commands allowed. RESTART_CONTROLLER blocked.",
            "FREEZE":         "SAFETY HOLD ACTIVE. All high-impact operations blocked. Read-only commands only.",
            "DOWNGRADE":      "Diagnostics mode. Only GET_STATUS and SIMULATE_SWITCH permitted.",
            "TIMEBOX_ACTIVE": "Supervisor-approved window. High-impact commands temporarily permitted.",
            "SAFE":           "Safe mode. Read-only only. Awaiting operator review.",
        }
        return {
            "mode":        mode,
            "description": descriptions.get(mode, "Unknown mode"),
            "barrier":     engine.barrier.status(),
        }

    # ── koral_get_session ─────────────────────────────────────────────────────
    elif name == "koral_get_session":
        last_n  = int(arguments.get("last_n", 20))
        session = engine.koral.get_session(last_n)
        status  = engine.koral.status()
        return {
            "agent":          "KORAL",
            "zone":           "Zone 3 — Reef",
            "total_observed": status.get("total_observed", 0),
            "session_length": status.get("session_length", 0),
            "records":        session,
        }

    # ── marea_get_signals ─────────────────────────────────────────────────────
    elif name == "marea_get_signals":
        snap    = engine._snapshot()
        log     = snap.get("gateway_log", [])
        signals = []
        for entry in log:
            for sig in entry.get("signals", []):
                signals.append({
                    **sig,
                    "command":  entry.get("command"),
                    "zone":     entry.get("zone"),
                    "asset_id": entry.get("asset_id"),
                    "ts":       entry.get("ts"),
                })
        return {
            "agent":        "MAREA",
            "zone":         "Zone 3 — Reef",
            "total_signals": len(signals),
            "signals":      signals,
        }

    # ── nereus_get_recommendation ─────────────────────────────────────────────
    elif name == "nereus_get_recommendation":
        snap = engine._snapshot()
        inc  = snap.get("active_incident")
        nereus_brief = snap.get("nereus_brief") or (inc.get("nereus_brief") if inc else None)
        return {
            "agent":          "NEREUS",
            "zone":           "Zone 3 — Reef",
            "tare_mode":      snap.get("mode", "NORMAL"),
            "recommendation": nereus_brief or "No active recommendation. NEREUS wakes only when ≥2 signals are detected.",
            "active_incident": {
                "id":       inc.get("incident_id"),
                "priority": inc.get("priority"),
                "state":    inc.get("state"),
            } if inc else None,
        }

    # ── echo_diagnose ─────────────────────────────────────────────────────────
    elif name == "echo_diagnose":
        snap    = engine._snapshot()
        signals = engine.anomaly_signals if hasattr(engine, "anomaly_signals") else []
        result  = engine.echo.diagnose(
            signals     = signals,
            zones       = engine.zones,
            assets      = engine.assets,
            gateway_log = engine.gateway_log,
            agent       = engine.agent,
        )
        return result

    # ── simar_simulate ────────────────────────────────────────────────────────
    elif name == "simar_simulate":
        steps = arguments.get("steps", [])
        if not steps:
            return {"error": "steps array is required with at least one {command, asset_id, zone}"}
        result = engine.simar.simulate(
            proposed_steps = steps,
            zones          = engine.zones,
            assets         = engine.assets,
        )
        return result

    # ── navis_build_plan ──────────────────────────────────────────────────────
    elif name == "navis_build_plan":
        # Run ECHO first to get latest diagnostic, then SIMAR, then NAVIS
        echo_result  = engine.echo.diagnose(
            signals     = getattr(engine, "anomaly_signals", []),
            zones       = engine.zones,
            assets      = engine.assets,
            gateway_log = engine.gateway_log,
            agent       = engine.agent,
        )
        simar_result = engine.simar.simulate(
            proposed_steps = echo_result.get("repair_actions", []),
            zones          = engine.zones,
            assets         = engine.assets,
        )
        plan = engine.navis.build_plan(
            echo_result  = echo_result,
            simar_result = simar_result,
            zones        = engine.zones,
            assets       = engine.assets,
            agent        = engine.agent,
        )
        return plan

    # ── riskador_score_plan ───────────────────────────────────────────────────
    elif name == "riskador_score_plan":
        # Build latest plan then score it
        echo_result  = engine.echo.diagnose(
            signals     = getattr(engine, "anomaly_signals", []),
            zones       = engine.zones,
            assets      = engine.assets,
            gateway_log = engine.gateway_log,
            agent       = engine.agent,
        )
        simar_result = engine.simar.simulate(
            proposed_steps = echo_result.get("repair_actions", []),
            zones          = engine.zones,
            assets         = engine.assets,
        )
        plan = engine.navis.build_plan(
            echo_result  = echo_result,
            simar_result = simar_result,
            zones        = engine.zones,
            assets       = engine.assets,
            agent        = engine.agent,
        )
        score = engine.riskador.score(
            plan        = plan,
            zones       = engine.zones,
            assets      = engine.assets,
            echo_result = echo_result,
        )
        return score

    # ── triton_get_status ─────────────────────────────────────────────────────
    elif name == "triton_get_status":
        return engine.triton.status()

    # ── tare_get_all_agents_status ────────────────────────────────────────────
    elif name == "tare_get_all_agents_status":
        return {
            "Zone 3 — Reef": {
                "KORAL":   engine.koral.status(),
                "MAREA":   engine.marea.status(),
                "TASYA":   engine.tasya.status(),
                "NEREUS":  engine.nereus.status(),
            },
            "Zone 2 — Shelf": {
                "ECHO":     engine.echo.status(),
                "SIMAR":    engine.simar.status(),
                "NAVIS":    engine.navis.status(),
                "RISKADOR": engine.riskador.status(),
            },
            "Zone 1 — Trench": {
                "TRITON":  engine.triton.status(),
                "AEGIS":   engine.aegis.status(),
                "TEMPEST": engine.tempest.status(),
                "LEVIER":  engine.levier.status(),
            },
            "Zone 4 — Policy": {
                "BARRIER": engine.barrier.status(),
            },
        }

    # ── tare_approve_timebox ──────────────────────────────────────────────────
    elif name == "tare_approve_timebox":
        engine.approve_timebox(duration_minutes=3)
        return {"status": "approved", "message": "3-minute timebox approved. BARRIER → TIMEBOX_ACTIVE."}

    # ── tare_deny_timebox ─────────────────────────────────────────────────────
    elif name == "tare_deny_timebox":
        engine.deny_timebox()
        return {"status": "denied", "message": "Timebox denied. BARRIER remains in FREEZE."}

    # ── tare_reset ────────────────────────────────────────────────────────────
    elif name == "tare_reset":
        engine.reset()
        return {"status": "reset", "message": "TARE session reset. All zones nominal. Mode → NORMAL."}

    # ── log_identity_action ───────────────────────────────────────────────────
    elif name == "log_identity_action":
        principal   = arguments.get("principal", "")
        action      = arguments.get("action", "")
        target_zone = arguments.get("target_zone", "")
        if not principal or not action or not target_zone:
            return {"error": "principal, action, and target_zone are required"}
        record = engine.koral.log_action(principal, action, target_zone)
        return {
            "logged":      True,
            "record":      record,
            "identity_log_total": len(engine.koral.get_identity_log()),
        }

    # ── check_identity_policy ─────────────────────────────────────────────────
    elif name == "check_identity_policy":
        principal   = arguments.get("principal", "")
        action      = arguments.get("action", "")
        target_zone = arguments.get("target_zone", "")
        if not principal or not action or not target_zone:
            return {"error": "principal, action, and target_zone are required"}
        return engine.check_identity_policy(principal, action, target_zone)

    # ── enforce_readonly_policy ───────────────────────────────────────────────
    elif name == "enforce_readonly_policy":
        principal = arguments.get("principal", "")
        action    = arguments.get("action", "")
        if not principal or not action:
            return {"error": "principal and action are required"}
        result = engine.barrier.enforce_readonly(principal, action)
        return {
            **result,
            "blocked_identities": list(engine.barrier._blocked_identities),
        }

    return {"error": f"Unknown tool: {name}"}


# ─── JSON-RPC Helpers ─────────────────────────────────────────────────────────

def _ok(result, req_id):
    return {"jsonrpc": "2.0", "result": result, "id": req_id}

def _err(code, message, req_id):
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": req_id}


# ─── MCP Endpoint ─────────────────────────────────────────────────────────────

@router.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Single MCP HTTP endpoint — handles all JSON-RPC methods BlueVerse sends.
    Register in BlueVerse as: MCP Remote - HTTP  →  <ngrok-url>/mcp
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_err(-32700, "Parse error — invalid JSON", None))

    method = body.get("method", "")
    req_id = body.get("id")
    params = body.get("params", {}) or {}

    # initialize
    if method == "initialize":
        return JSONResponse(_ok({
            "protocolVersion": "2024-11-05",
            "capabilities":    {"tools": {}},
            "serverInfo":      {"name": "AEGIS-ID TARE MCP Server", "version": "1.0.0"},
        }, req_id))

    # initialized notification — no response body needed
    if method == "notifications/initialized":
        return JSONResponse({})

    # tools/list
    if method == "tools/list":
        return JSONResponse(_ok({"tools": TOOLS}, req_id))

    # tools/call
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {}) or {}

        engine = getattr(request.app.state, "tare_engine", None)
        if engine is None:
            return JSONResponse(_err(-32603, "TARE engine not available", req_id))

        try:
            result = _execute_tool(tool_name, arguments, engine)
        except Exception as e:
            return JSONResponse(_err(-32603, f"Tool execution error: {str(e)}", req_id))

        return JSONResponse(_ok({
            "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
        }, req_id))

    return JSONResponse(_err(-32601, f"Method not found: {method}", req_id))
