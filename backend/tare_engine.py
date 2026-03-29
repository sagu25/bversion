"""
TARE Engine — Trusted Access Response Engine
Post-grant identity response layer for Energy & Utilities
"""
import time
import threading
import uuid
import os
from datetime import datetime
from collections import deque

# ─── ML Detector (optional — graceful fallback if model not trained yet) ───────
try:
    from ml_detector import MLDetector
    _ml = MLDetector()
except Exception:
    _ml = None

# ─── Groq LLM (optional — falls back to static if key not set) ────────────────
try:
    from groq import Groq
    _groq_key = os.environ.get("GROQ_API_KEY", "")
    _groq_client = Groq(api_key=_groq_key) if _groq_key else None
    _LLM_AVAILABLE = bool(_groq_key)
except Exception:
    _groq_client = None
    _LLM_AVAILABLE = False

# ─── Zone Definitions ──────────────────────────────────────────────────────────
ZONES = {
    "Z1": {"id": "Z1", "name": "Zone 1 — North Grid", "health": "HEALTHY", "fault": None,   "color": "green"},
    "Z2": {"id": "Z2", "name": "Zone 2 — East Grid",  "health": "HEALTHY", "fault": None,   "color": "green"},
    "Z3": {"id": "Z3", "name": "Zone 3 — West Grid",  "health": "HEALTHY", "fault": None, "color": "green"},
}

# ─── Asset Definitions ─────────────────────────────────────────────────────────
INITIAL_ASSETS = {
    "BRK-301": {"id": "BRK-301", "type": "BREAKER", "zone": "Z3", "state": "CLOSED",    "description": "Main Circuit Breaker Z3"},
    "FDR-301": {"id": "FDR-301", "type": "FEEDER",  "zone": "Z3", "state": "RUNNING",   "description": "Feeder Controller Z3"},
    "BRK-205": {"id": "BRK-205", "type": "BREAKER", "zone": "Z2", "state": "CLOSED",    "description": "Main Circuit Breaker Z2"},
    "FDR-205": {"id": "FDR-205", "type": "FEEDER",  "zone": "Z2", "state": "RUNNING",   "description": "Feeder Controller Z2"},
    "BRK-110": {"id": "BRK-110", "type": "BREAKER", "zone": "Z1", "state": "CLOSED",    "description": "Main Circuit Breaker Z1"},
    "FDR-110": {"id": "FDR-110", "type": "FEEDER",  "zone": "Z1", "state": "RUNNING",   "description": "Feeder Controller Z1"},
}

# ─── Operator Agent ────────────────────────────────────────────────────────────
OPERATOR_AGENT = {
    "id":             "OP-GRID-7749",
    "name":           "GridOperator-Agent",
    "role":           "GRID_OPERATOR",
    "clearance":      "LEVEL_3",
    "department":     "Grid Operations",
    "rbac_zones":     ["Z1", "Z2", "Z3"],   # Cleared for all three zones
    "assigned_zone":  "Z3",                  # Active work order: Z3 fault repair
    "rbac_token":     "eyJhbGciOiJSUzI1NiJ9.TARE-MOCK-TOKEN",
    "status":         "ACTIVE",
    "action_count":   0,
    "last_command":   None,
    "last_result":    None,
}

# ─── Command Classification ────────────────────────────────────────────────────
HIGH_IMPACT = {"OPEN_BREAKER", "CLOSE_BREAKER", "RESTART_CONTROLLER", "EMERGENCY_SHUTDOWN"}
NEEDS_SIMULATION = {"OPEN_BREAKER"}          # must SIMULATE_SWITCH first
READ_ONLY = {"GET_STATUS", "GET_TELEMETRY"}
SIMULATION_CMDS = {"SIMULATE_SWITCH"}

# ─── TARE Engine ───────────────────────────────────────────────────────────────
class TAREEngine:
    def __init__(self, broadcast_fn=None):
        self._broadcast = broadcast_fn or (lambda _: None)
        self._lock = threading.Lock()

        # Mode: NORMAL | FREEZE | DOWNGRADE | TIMEBOX_ACTIVE | SAFE
        self.mode = "NORMAL"
        self.mode_changed_at = None
        self.previous_mode = None

        # Assets (mutable copy)
        self.assets = {k: dict(v) for k, v in INITIAL_ASSETS.items()}
        self.zones  = {k: dict(v) for k, v in ZONES.items()}

        # Agent state
        self.agent = dict(OPERATOR_AGENT)

        # Command history
        self.command_history = deque(maxlen=100)
        self.burst_window     = deque(maxlen=50)   # timestamps for burst detection

        # Simulation tracker: agent_id -> last_simulate_ts
        self.last_simulated = {}

        # Gateway log (last 30)
        self.gateway_log = []

        # Zone access log (for observability panel)
        self.zone_access_log = []

        # Active anomaly
        self.anomaly_signals = []
        self.anomaly_score   = 0

        # ServiceNow incident
        self.active_incident = None

        # Time-box
        self.timebox_expires = None
        self.timebox_total   = 0
        self._timebox_thread = None

        # Stats
        self.stats = {"total": 0, "allowed": 0, "denied": 0, "freeze_events": 0}

        # ML detector
        self.ml_detector = _ml

    # ─── Public API ────────────────────────────────────────────────────────────
    def inject_fault(self, zone_id: str, fault_msg: str):
        """Introduce a fault into a zone — used to simulate fault before repair scenario."""
        with self._lock:
            zone = self.zones.get(zone_id)
            if zone:
                zone["health"] = "FAULT"
                zone["fault"]  = fault_msg
                zone["color"]  = "red"

    def reset(self):
        with self._lock:
            self.mode           = "NORMAL"
            self.mode_changed_at = None
            self.previous_mode  = None
            self.assets         = {k: dict(v) for k, v in INITIAL_ASSETS.items()}
            self.zones          = {k: dict(v) for k, v in ZONES.items()}
            self.agent          = dict(OPERATOR_AGENT)
            self.command_history.clear()
            self.burst_window.clear()
            self.last_simulated.clear()
            self.gateway_log    = []
            self.zone_access_log= []
            self.anomaly_signals= []
            self.anomaly_score  = 0
            self.active_incident= None
            self.timebox_expires= None
            self.timebox_total  = 0
            self.stats          = {"total": 0, "allowed": 0, "denied": 0, "freeze_events": 0}

        self._broadcast({"type": "RESET", "message": "System reset. All zones nominal. TARE in NORMAL mode."})
        self._broadcast(self._snapshot())

    def process_command(self, command, asset_id, zone, skip_sim=False, token=None):
        """Main gateway entry — every command passes through here."""

        # ── Identity check (pre-grant) ──────────────────────────────────────
        if token is not None and token != self.agent["rbac_token"]:
            rec_id = str(uuid.uuid4())[:8]
            ts     = datetime.now().isoformat()
            entry  = {
                "id":       rec_id,
                "ts":       ts,
                "command":  command,
                "asset_id": asset_id,
                "zone":     zone,
                "decision": "DENY",
                "reason":   "IDENTITY_MISMATCH — token fingerprint does not match registered credential",
                "policy":   "POL-AUTH-001",
                "mode":     self.mode,
                "signals":  [{"signal": "IDENTITY_MISMATCH",
                               "detail": f"Presented token '{token[:28]}…' rejected — not a registered agent",
                               "severity": "CRITICAL"}],
            }
            with self._lock:
                self.stats["total"]  += 1
                self.stats["denied"] += 1
                self.gateway_log.insert(0, entry)
                self.gateway_log = self.gateway_log[:30]

            self._broadcast({"type": "GATEWAY_DECISION", **entry})
            self._broadcast({
                "type":    "IDENTITY_ALERT",
                "id":      rec_id,
                "ts":      ts,
                "command": command,
                "token":   token,
                "message": "Forged credential detected — access blocked at authentication layer",
            })

            # Create ServiceNow incident for identity impersonation attempt
            with self._lock:
                if self.active_incident is None:
                    incident_id = f"INC-TARE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4().int)[:4]}"
                    self.active_incident = {
                        "incident_id":       incident_id,
                        "short_description": "Identity impersonation attempt — forged token blocked at authentication layer",
                        "priority":          self._incident_priority(entry["signals"]),
                        "state":             "New",
                        "assigned_to":       "SOC Analyst",
                        "category":          "Security / Identity",
                        "created_at":        ts,
                        "evidence": {
                            "anomaly_signals": entry["signals"],
                            "anomaly_score":   100,
                            "recent_commands": [],
                            "actions_taken":   [
                                "IDENTITY_MISMATCH — token rejected before any command reached the grid",
                                "ServiceNow INC created — SOC Analyst assigned",
                            ],
                        },
                    }
                    self._broadcast({"type": "SERVICENOW_INCIDENT", "incident": self.active_incident})

            self._broadcast({
                "type":    "CHAT_MESSAGE",
                "role":    "tare",
                "message": (
                    f"IDENTITY ALERT: An agent presented a cloned identity with a forged credential token. "
                    f"The token fingerprint did not match any registered agent — '{command}' on {asset_id} "
                    f"was blocked at the authentication layer before reaching the grid. "
                    f"A Critical ServiceNow incident has been raised and assigned to the SOC Analyst for investigation."
                ),
            })
            self._broadcast(self._snapshot())
            return {"decision": "DENY", "reason": "IDENTITY_MISMATCH", "policy": "POL-AUTH-001", "mode": self.mode}

        now = time.time()
        with self._lock:
            self.stats["total"] += 1
            self.burst_window.append(now)
            self.agent["action_count"] += 1
            self.agent["last_command"] = command

            # Record in history
            rec = {
                "id":       str(uuid.uuid4())[:8],
                "ts":       datetime.now().isoformat(),
                "ts_epoch": now,
                "command":  command,
                "asset_id": asset_id,
                "zone":     zone,
                "skip_sim": skip_sim,
            }
            self.command_history.append(rec)
            self.zone_access_log.append(rec)

            # --- Deviation detection (only fires in NORMAL mode) ---
            signals = []
            if self.mode == "NORMAL":
                signals = self._detect_signals(command, zone, skip_sim, now)
                if len(signals) >= 2:
                    # Score ≥ 50 → TARE fires
                    self._fire_tare(signals)

            # --- Gateway decision ---
            decision, reason, policy = self._gateway_policy(command, zone)
            self.agent["last_result"] = decision

            log_entry = {
                "id":       rec["id"],
                "ts":       rec["ts"],
                "command":  command,
                "asset_id": asset_id,
                "zone":     zone,
                "decision": decision,
                "reason":   reason,
                "policy":   policy,
                "mode":     self.mode,
                "signals":  signals,
            }
            self.gateway_log.insert(0, log_entry)
            self.gateway_log = self.gateway_log[:30]

            if decision == "ALLOW":
                self.stats["allowed"] += 1
                self._apply_asset_change(command, asset_id)
            else:
                self.stats["denied"] += 1

            # Track simulation step
            if command in SIMULATION_CMDS:
                self.last_simulated[self.agent["id"]] = now

        self._broadcast({
            "type":     "GATEWAY_DECISION",
            "id":       rec["id"],
            "ts":       rec["ts"],
            "command":  command,
            "asset_id": asset_id,
            "zone":     zone,
            "decision": decision,
            "reason":   reason,
            "policy":   policy,
            "mode":     self.mode,
            "signals":  signals,
        })
        self._broadcast(self._snapshot())
        return {"decision": decision, "reason": reason, "policy": policy, "mode": self.mode}

    def approve_timebox(self, duration_minutes=3):
        with self._lock:
            self._set_mode("TIMEBOX_ACTIVE")
            self.timebox_expires = time.time() + duration_minutes * 60
            self.timebox_total   = duration_minutes * 60

        self._broadcast({
            "type":             "TIMEBOX_APPROVED",
            "duration_minutes": duration_minutes,
            "expires_at":       self.timebox_expires,
            "message":          f"Supervisor approved {duration_minutes}-minute time-box. OPEN_BREAKER re-enabled. RESTART_CONTROLLER remains blocked.",
        })
        self._broadcast({
            "type":    "CHAT_MESSAGE",
            "role":    "tare",
            "message": f"Time-box approved. Switching commands re-enabled for {duration_minutes} minutes. RESTART_CONTROLLER remains permanently blocked — strong safety posture maintained. System will auto-revert to SAFE mode when the window expires.",
        })
        self._broadcast(self._snapshot())
        self._start_countdown(duration_minutes * 60)

    def deny_timebox(self):
        with self._lock:
            self._set_mode("SAFE")
            if self.active_incident:
                self.active_incident["state"]       = "Escalated"
                self.active_incident["escalated_at"] = datetime.now().isoformat()

        self._broadcast({
            "type":    "TIMEBOX_DENIED",
            "message": "Supervisor denied time-box request. Incident escalated.",
        })
        self._broadcast({
            "type":    "CHAT_MESSAGE",
            "role":    "tare",
            "message": (
                "Supervisor has denied the time-box request. "
                "System remains in SAFE mode — all high-impact operations are permanently blocked "
                "until a full investigation is complete. "
                "ServiceNow incident has been escalated to Critical response. "
                "GridOperator-Agent is locked out pending review."
            ),
            "show_approve": False,
        })
        self._broadcast(self._snapshot())

    # ─── Demo Sequences ────────────────────────────────────────────────────────
    def run_normal_ops(self):
        """3 authorised commands in Z3 (fault zone) — all ALLOWED."""
        def _seq():
            self._broadcast({"type": "CHAT_MESSAGE", "role": "system",
                "message": "Running baseline operations — 3 commands in authorised Zone Z3 (active fault zone)..."})
            cmds = [
                ("GET_STATUS",       "BRK-301", "Z3"),
                ("SIMULATE_SWITCH",  "BRK-301", "Z3"),
                ("OPEN_BREAKER",     "BRK-301", "Z3"),
            ]
            for cmd, asset, zone in cmds:
                time.sleep(1.8)
                self.process_command(cmd, asset, zone)
        threading.Thread(target=_seq, daemon=True).start()

    def trigger_anomaly(self):
        """Burst + wrong zone + healthy zone + skipped sim → TARE fires."""
        def _seq():
            self._broadcast({"type": "CHAT_MESSAGE", "role": "system",
                "message": "Anomalous behaviour pattern initiated — agent targeting healthy Zone Z1 at burst rate, skipping safety simulation..."})
            cmds = [
                ("GET_STATUS",          "BRK-110", "Z1", False),
                ("OPEN_BREAKER",        "BRK-110", "Z1", True),   # skip_sim, wrong zone, healthy zone
                ("OPEN_BREAKER",        "FDR-110", "Z1", True),
                ("RESTART_CONTROLLER",  "FDR-110", "Z1", True),
            ]
            for cmd, asset, zone, skip in cmds:
                time.sleep(0.4)   # burst rate
                self.process_command(cmd, asset, zone, skip_sim=skip)
        threading.Thread(target=_seq, daemon=True).start()

    # ─── Internal: Detection ───────────────────────────────────────────────────
    def _detect_signals(self, command, zone, skip_sim, now):
        signals = []

        # Signal 1 — Burst rate
        recent = [t for t in self.burst_window if now - t < 10]
        if len(recent) > 3:
            signals.append({
                "signal":   "BURST_RATE",
                "detail":   f"{len(recent)} commands in 10 s (threshold: 3)",
                "severity": "HIGH",
            })

        # Signal 2 — Outside active task zone (agent has clearance, but no work order here)
        assigned = self.agent.get("assigned_zone", "Z3")
        if zone != assigned:
            signals.append({
                "signal":   "OUT_OF_ZONE",
                "detail":   f"Active task zone is {assigned} (fault repair) — no work order for {zone}",
                "severity": "HIGH",
            })

        # Signal 3 — Healthy-zone access (high-impact on a zone with no fault)
        zone_data = self.zones.get(zone, {})
        if zone_data.get("health") == "HEALTHY" and command in HIGH_IMPACT:
            signals.append({
                "signal":   "HEALTHY_ZONE_ACCESS",
                "detail":   f"{zone} is HEALTHY (no fault) — high-impact command unprovoked",
                "severity": "CRITICAL",
            })

        # Signal 4 — Skipped simulation
        if command in NEEDS_SIMULATION and skip_sim:
            last_sim = self.last_simulated.get(self.agent["id"], 0)
            if now - last_sim > 60:
                signals.append({
                    "signal":   "SKIPPED_SIMULATION",
                    "detail":   "OPEN_BREAKER without prior SIMULATE_SWITCH in last 60 s",
                    "severity": "MEDIUM",
                })

        # Signal 5 — ML anomaly detector (catches patterns rules miss, e.g. slow & low recon)
        if self.ml_detector and self.ml_detector.available:
            history = list(self.command_history)[-20:]
            recent_cmds = [
                {"command": r["command"], "zone": r["zone"],
                 "ts": r.get("ts_epoch", now)}
                for r in history
            ]
            zone_health = {k: v["health"] for k, v in self.zones.items()}
            ml_result   = self.ml_detector.score(recent_cmds, zone_health)
            for sig in ml_result.get("signals", []):
                signals.append(sig)

        return signals

    # ─── Internal: Gateway Policy ──────────────────────────────────────────────
    def _gateway_policy(self, command, zone):
        m = self.mode
        if m == "NORMAL":
            if command == "RESTART_CONTROLLER":
                return "DENY", "RESTART_CONTROLLER not in RBAC claims", "POL-RBAC-001"
            return "ALLOW", "Within RBAC and baseline policy", "POL-NORMAL-001"

        elif m == "FREEZE":
            if command in READ_ONLY:
                return "ALLOW", "Read-only permitted during FREEZE", "POL-FREEZE-002"
            return "DENY", "SAFETY HOLD ACTIVE — high-impact operations frozen", "POL-FREEZE-001"

        elif m == "DOWNGRADE":
            if command in READ_ONLY | SIMULATION_CMDS:
                return "ALLOW", "Diagnostics / simulation permitted in DOWNGRADE", "POL-DOWN-001"
            return "DENY", "DOWNGRADE mode — operational commands restricted", "POL-DOWN-002"

        elif m == "TIMEBOX_ACTIVE":
            if command == "RESTART_CONTROLLER":
                return "DENY", "RESTART_CONTROLLER remains blocked — not in time-box scope", "POL-TIMEBOX-002"
            if command in HIGH_IMPACT:
                rem = max(0, int(self.timebox_expires - time.time())) if self.timebox_expires else 0
                return "ALLOW", f"TIME-BOX ACTIVE — {rem}s remaining in approved window", "POL-TIMEBOX-001"
            return "ALLOW", "TIME-BOX ACTIVE — within approved window", "POL-TIMEBOX-001"

        elif m == "SAFE":
            if command in READ_ONLY:
                return "ALLOW", "Safe mode — read-only permitted", "POL-SAFE-001"
            return "DENY", "Safe mode — awaiting operator review before resuming ops", "POL-SAFE-002"

        return "DENY", "Unknown policy mode", "POL-ERR-001"

    # ─── LLM Explanation ───────────────────────────────────────────────────────
    def _llm_explain(self, signals, recent_commands):
        """Call Groq LLM to generate a dynamic TARE explanation. Falls back to static."""
        if not _LLM_AVAILABLE or not _groq_client:
            return self._static_explain(signals)
        try:
            sig_text = "\n".join(f"- {s['signal']} ({s['severity']}): {s['detail']}" for s in signals)
            cmd_text = "\n".join(f"- {c['command']} on {c['asset_id']} in {c['zone']}" for c in recent_commands[-5:])
            agent_name     = self.agent.get("name", "GridOperator-Agent")
            agent_id       = self.agent.get("id", "OP-GRID-7749")
            assigned_zone  = self.agent.get("assigned_zone", "Z3")
            rbac_zones     = self.agent.get("rbac_zones", [])
            attacked_zones = list({c["zone"] for c in recent_commands if c["zone"] != assigned_zone})
            rbac_str       = ", ".join(rbac_zones) if rbac_zones else "none"
            attacked_str   = ", ".join(attacked_zones) if attacked_zones else "none detected"

            prompt = f"""You are TARE, a Trusted Access Response Engine for an energy grid security platform.
A behavioural anomaly has been detected and you have frozen high-impact operations. Brief the human supervisor.

RAW EVIDENCE:
Agent: {agent_name} (ID: {agent_id})
Clearance zones: {rbac_str}
Active work order: {assigned_zone}
Anomaly signals fired: {sig_text}
Recent commands: {cmd_text}

Write a 3-4 sentence briefing for the supervisor. Include: what the agent did, why it is suspicious given its work order, what TARE has done in response, and what decision the supervisor must make (approve a 3-minute time-box or deny and escalate). Be specific about zones and commands. Do not use bullet points."""

            for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
                try:
                    response = _groq_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=180,
                        temperature=0.4,
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(3)
                        continue
                    break
            return self._static_explain(signals)
        except Exception:
            return self._static_explain(signals)

    def _static_explain(self, signals):
        agent_name    = self.agent.get("name", "GridOperator-Agent")
        assigned_zone = self.agent.get("assigned_zone", "Z3")
        recent        = list(self.command_history)[-20:]
        off_task      = list({c["zone"] for c in recent if c["zone"] != assigned_zone})
        sig_names     = ", ".join(s["signal"] for s in signals)
        zones_str     = ", ".join(off_task) if off_task else "zones outside active task"
        return (
            f"{agent_name} has been frozen due to behavioural anomalies: {sig_names}. "
            f"The agent has valid credentials and clearance for all zones, but its active work order "
            f"is {assigned_zone} (fault repair). It accessed {zones_str}, which have no active fault "
            f"and no work order requiring action there. "
            f"TARE has applied FREEZE and downgraded access to read-only. "
            f"Please review the evidence and decide whether to approve a 3-minute time-box or escalate."
        )

    # ─── Priority based on highest-risk zone involved ───────────────────────────
    def _incident_priority(self, signals=None):
        """
        P1 Critical  — identity breach, burst-rate, or high-impact attack on a healthy zone
        P2 High      — quiet out-of-zone escalation or ML-only recon (read-only, no burst)
        P3 Medium    — Z3-only, authorised zone, low-impact
        """
        sig_names = {s["signal"] for s in (signals or [])}
        if "IDENTITY_MISMATCH" in sig_names or "BURST_RATE" in sig_names or "HEALTHY_ZONE_ACCESS" in sig_names:
            return "1 — Critical"
        if "OUT_OF_ZONE" in sig_names or "ML_ANOMALY" in sig_names:
            return "2 — High"
        return "3 — Medium"

    # ─── Internal: TARE Response ───────────────────────────────────────────────
    def _fire_tare(self, signals):
        self._set_mode("FREEZE")
        self.anomaly_signals = signals
        self.anomaly_score   = len(signals) * 25
        self.stats["freeze_events"] += 1

        # Build evidence
        recent = list(self.command_history)[-20:]
        evidence = {
            "anomaly_signals": signals,
            "anomaly_score":   self.anomaly_score,
            "recent_commands": recent,
            "actions_taken":   [
                "FREEZE — high-impact operations halted immediately",
                "DOWNGRADE — privileges reduced to read-only + diagnostics",
            ],
        }

        # ServiceNow incident
        incident_id = f"INC-TARE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4().int)[:4]}"
        self.active_incident = {
            "incident_id":       incident_id,
            "short_description": "Post-grant identity behaviour deviation detected — operations frozen",
            "priority":          self._incident_priority(signals),
            "state":             "New",
            "assigned_to":       "SOC Analyst",
            "category":          "Security / Identity",
            "created_at":        datetime.now().isoformat(),
            "evidence":          evidence,
        }

        self._broadcast({
            "type":    "TARE_RESPONSE",
            "action":  "FREEZE",
            "mode":    "FREEZE",
            "signals": signals,
            "score":   self.anomaly_score,
            "message": "High-impact grid operations FROZEN due to behavioural deviation",
        })
        self._broadcast({"type": "SERVICENOW_INCIDENT", "incident": self.active_incident})

        # Downgrade after short delay — explanation fires at downgrade time
        # so the LLM sees the full picture (all zones attacked, not just the first)
        threading.Timer(2.5, self._apply_downgrade, args=(signals,)).start()

    def _apply_downgrade(self, signals=None):
        with self._lock:
            if self.mode == "FREEZE":
                self._set_mode("DOWNGRADE")
        self._broadcast({
            "type":    "TARE_RESPONSE",
            "action":  "DOWNGRADE",
            "mode":    "DOWNGRADE",
            "message": "Privileges downgraded to read-only + diagnostics. High-impact commands blocked.",
        })
        self._broadcast(self._snapshot())

        # Update incident evidence now — captures all commands during the FREEZE window
        if self.active_incident is not None:
            recent_cmds = list(self.command_history)[-30:]
            self.active_incident["evidence"]["recent_commands"] = recent_cmds
            self.active_incident["evidence"]["actions_taken"].append(
                "ServiceNow INC created — SOC Analyst assigned"
            )
            self._broadcast({"type": "SERVICENOW_INCIDENT", "incident": self.active_incident})
            self._broadcast(self._snapshot())

        # Generate explanation now — captures all zones attacked during the FREEZE window
        if signals is not None:
            recent      = list(self.command_history)[-30:]
            explanation = self._llm_explain(signals, recent)
            self._broadcast({
                "type":       "CHAT_MESSAGE",
                "role":       "tare",
                "message":    explanation,
                "show_approve": True,
            })

    def _set_mode(self, new_mode):
        self.previous_mode   = self.mode
        self.mode            = new_mode
        self.mode_changed_at = datetime.now().isoformat()

    def _apply_asset_change(self, command, asset_id):
        asset = self.assets.get(asset_id)
        if not asset:
            return
        if command == "OPEN_BREAKER":
            asset["state"] = "OPEN"
            # If the breaker being opened is in a FAULT zone, the fault is resolved
            zone_id = asset.get("zone")
            zone = self.zones.get(zone_id, {})
            if zone.get("health") == "FAULT":
                zone["health"] = "HEALTHY"
                zone["fault"]  = None
                zone["color"]  = "green"
        elif command == "CLOSE_BREAKER":
            asset["state"] = "CLOSED"
        elif command == "RESTART_CONTROLLER":
            asset["state"] = "RESTARTING"

    # ─── Internal: Time-box ────────────────────────────────────────────────────
    def _start_countdown(self, total_seconds):
        def _tick():
            remaining = total_seconds
            while remaining > 0:
                time.sleep(1)
                remaining -= 1
                with self._lock:
                    if self.mode != "TIMEBOX_ACTIVE":
                        return
                if remaining % 10 == 0 or remaining <= 10:
                    self._broadcast({"type": "TIMEBOX_TICK",
                                     "remaining_seconds": remaining,
                                     "total_seconds": total_seconds})
            self._expire_timebox()
        self._timebox_thread = threading.Thread(target=_tick, daemon=True)
        self._timebox_thread.start()

    def _expire_timebox(self):
        with self._lock:
            if self.mode == "TIMEBOX_ACTIVE":
                self._set_mode("SAFE")
                self.timebox_expires = None

        self._broadcast({"type": "TIMEBOX_EXPIRED", "mode": "SAFE",
                          "message": "Time-boxed access expired. System returned to constrained (safe) mode."})
        self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                          "message": "Time-boxed access expired. System has automatically returned to SAFE mode. All high-impact operations are blocked until a new approval is granted.",
                          "show_approve": False})
        self._broadcast(self._snapshot())

    # ─── Snapshot ──────────────────────────────────────────────────────────────
    def _snapshot(self):
        remaining = None
        if self.mode == "TIMEBOX_ACTIVE" and self.timebox_expires:
            remaining = max(0, int(self.timebox_expires - time.time()))

        return {
            "type":             "STATE_SNAPSHOT",
            "mode":             self.mode,
            "previous_mode":    self.previous_mode,
            "mode_changed_at":  self.mode_changed_at,
            "zones":            {k: dict(v) for k, v in self.zones.items()},
            "assets":           {k: dict(v) for k, v in self.assets.items()},
            "agent":            dict(self.agent),
            "gateway_log":      self.gateway_log[:15],
            "zone_access_log":  list(self.zone_access_log)[-20:],
            "anomaly_signals":  self.anomaly_signals,
            "anomaly_score":    self.anomaly_score,
            "active_incident":  self.active_incident,
            "stats":            dict(self.stats),
            "timebox_remaining":remaining,
            "timebox_total":    self.timebox_total,
        }
