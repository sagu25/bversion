"""
TARE Engine — Trusted Access Response Engine
Central orchestrator of the full 12-agent security system.

TARE decides. TARE never executes.
Agents wake, do their part, and go back to sleep.

Detection flow (every command):
    KORAL observes → BARRIER enforces
    If NORMAL: MAREA analyzes → TASYA correlates
    If ≥2 signals: NEREUS recommends → TARE decides FREEZE
    BARRIER.set_mode("FREEZE") → ServiceNow → LLM brief → Approve/Deny UI

Post-approval pipeline (Zone 2 → Zone 1):
    ECHO diagnoses → SIMAR simulates → NAVIS plans → RISKADOR scores
    → TARE issues permit → TRITON arms + AEGIS arms + TEMPEST arms + LEVIER arms
    → For each step: AEGIS validates → TRITON executes → TEMPEST monitors
    → On failure: LEVIER rolls back

All 4 zones:
    Zone 3 (Reef)  — KORAL, MAREA, TASYA, NEREUS   [Observe & Recommend]
    Zone 2 (Shelf) — ECHO, SIMAR, NAVIS, RISKADOR   [Diagnose & Prepare]
    Zone 1 (Trench)— TRITON, AEGIS, TEMPEST, LEVIER  [Execute with Safety]
    Zone 4         — BARRIER                          [Policy Enforcement]
"""
import time
import threading
import uuid
from datetime import datetime
from servicenow_client import ServiceNowClient
from models import TicketFields
from agents import (
    KORAL, MAREA, TASYA, NEREUS,          # Zone 3 — Reef (implemented)
    ECHO, SIMAR, NAVIS, RISKADOR,          # Zone 2 — Shelf (stubs)
    TRITON, AEGIS, TEMPEST, LEVIER,        # Zone 1 — Trench (stubs)
    BARRIER,                               # Zone 4 — Policy Enforcement
)

_snow_client = ServiceNowClient()

# ─── ML Detector (optional) ───────────────────────────────────────────────────
try:
    from ml_detector import MLDetector
    _ml = MLDetector()
except Exception:
    _ml = None

# ─── Zone Definitions ─────────────────────────────────────────────────────────
ZONES = {
    "Z1": {"id": "Z1", "name": "Zone 1 — North Grid", "health": "HEALTHY", "fault": None, "color": "green"},
    "Z2": {"id": "Z2", "name": "Zone 2 — East Grid",  "health": "HEALTHY", "fault": None, "color": "green"},
    "Z3": {"id": "Z3", "name": "Zone 3 — West Grid",  "health": "HEALTHY", "fault": None, "color": "green"},
}

# ─── Asset Definitions ────────────────────────────────────────────────────────
INITIAL_ASSETS = {
    "BRK-301": {"id": "BRK-301", "type": "BREAKER", "zone": "Z3", "state": "CLOSED",  "description": "Main Circuit Breaker Z3"},
    "FDR-301": {"id": "FDR-301", "type": "FEEDER",  "zone": "Z3", "state": "RUNNING", "description": "Feeder Controller Z3"},
    "BRK-205": {"id": "BRK-205", "type": "BREAKER", "zone": "Z2", "state": "CLOSED",  "description": "Main Circuit Breaker Z2"},
    "FDR-205": {"id": "FDR-205", "type": "FEEDER",  "zone": "Z2", "state": "RUNNING", "description": "Feeder Controller Z2"},
    "BRK-110": {"id": "BRK-110", "type": "BREAKER", "zone": "Z1", "state": "CLOSED",  "description": "Main Circuit Breaker Z1"},
    "FDR-110": {"id": "FDR-110", "type": "FEEDER",  "zone": "Z1", "state": "RUNNING", "description": "Feeder Controller Z1"},
}

# ─── Operator Agent ───────────────────────────────────────────────────────────
OPERATOR_AGENT = {
    "id":            "OP-GRID-7749",
    "name":          "GridOperator-Agent",
    "role":          "GRID_OPERATOR",
    "clearance":     "LEVEL_3",
    "department":    "Grid Operations",
    "rbac_zones":    ["Z1", "Z2", "Z3"],
    "assigned_zone": "Z3",
    "rbac_token":    "eyJhbGciOiJSUzI1NiJ9.TARE-MOCK-TOKEN",
    "status":        "ACTIVE",
    "action_count":  0,
    "last_command":  None,
    "last_result":   None,
}

HIGH_IMPACT = {"OPEN_BREAKER", "CLOSE_BREAKER", "RESTART_CONTROLLER", "EMERGENCY_SHUTDOWN"}
READ_ONLY   = {"GET_STATUS"}


# ─── TARE Engine ──────────────────────────────────────────────────────────────
class TAREEngine:
    """
    Central orchestrator. Decides. Never executes.
    Instantiates all agents and coordinates their activation.
    """

    def __init__(self, broadcast_fn=None):
        self._broadcast = broadcast_fn or (lambda _: None)
        self._lock      = threading.Lock()

        # ── Instantiate all agents ─────────────────────────────────────────────
        # Zone 3 — Reef (implemented)
        self.koral    = KORAL()
        self.marea    = MAREA(ml_detector=_ml)
        self.tasya    = TASYA()
        self.nereus   = NEREUS()
        # Zone 2 — Shelf (stubs, Phase 2)
        self.echo     = ECHO()
        self.simar    = SIMAR()
        self.navis    = NAVIS()
        self.riskador = RISKADOR()
        # Zone 1 — Trench (stubs, Phase 2)
        self.triton   = TRITON()
        self.aegis    = AEGIS()
        self.tempest  = TEMPEST()
        self.levier   = LEVIER()
        # Zone 4 — Policy Enforcement (implemented)
        self.barrier  = BARRIER()

        # ── TARE state ────────────────────────────────────────────────────────
        self.mode            = "NORMAL"
        self.mode_changed_at = None
        self.previous_mode   = None

        self.assets = {k: dict(v) for k, v in INITIAL_ASSETS.items()}
        self.zones  = {k: dict(v) for k, v in ZONES.items()}
        self.agent  = dict(OPERATOR_AGENT)

        self.gateway_log     = []
        self.anomaly_signals = []
        self.anomaly_score   = 0
        self.active_incident = None

        self.timebox_expires = None
        self.timebox_total   = 0
        self._timebox_thread = None

        self.stats = {"total": 0, "allowed": 0, "denied": 0, "freeze_events": 0}

    # ── Public API ─────────────────────────────────────────────────────────────

    def inject_fault(self, zone_id: str, fault_msg: str):
        with self._lock:
            zone = self.zones.get(zone_id)
            if zone:
                zone["health"] = "FAULT"
                zone["fault"]  = fault_msg
                zone["color"]  = "red"

    def reset(self):
        with self._lock:
            self.mode            = "NORMAL"
            self.mode_changed_at = None
            self.previous_mode   = None
            self.assets          = {k: dict(v) for k, v in INITIAL_ASSETS.items()}
            self.zones           = {k: dict(v) for k, v in ZONES.items()}
            self.agent           = dict(OPERATOR_AGENT)
            self.gateway_log     = []
            self.anomaly_signals = []
            self.anomaly_score   = 0
            self.active_incident = None
            self.timebox_expires = None
            self.timebox_total   = 0
            self.stats           = {"total": 0, "allowed": 0, "denied": 0, "freeze_events": 0}

            # Reset all agents
            self.koral.clear()
            self.marea.clear_sim_tracker()
            self.barrier.reset()
            self.aegis.reset()
            self.tempest.reset()
            self.triton.reset()
            self.levier.reset()

        self._broadcast({"type": "RESET", "message": "System reset. All zones nominal. TARE in NORMAL mode."})
        self._broadcast(self._snapshot())

    def process_command(self, command, asset_id, zone, skip_sim=False, token=None):
        """
        Main gateway entry point. Every command passes through here.

        Orchestration flow:
          1. Pre-grant identity check (token fingerprint)
          2. KORAL observes the command
          3. BARRIER enforces current mode → ALLOW / DENY
          4. If NORMAL mode: MAREA analyzes for drift signals
          5. If signals found: TASYA correlates with context
          6. If ≥2 signals: NEREUS recommends action to TARE
          7. TARE decides and instructs BARRIER to update mode
        """

        # ── Step 1: Pre-grant identity check ──────────────────────────────────
        if token is not None and token != self.agent["rbac_token"]:
            return self._handle_identity_mismatch(command, asset_id, zone, token)

        now = time.time()
        ts  = datetime.now().isoformat()

        with self._lock:
            self.stats["total"] += 1
            self.agent["action_count"] += 1
            self.agent["last_command"]  = command

            rec = {
                "id":       str(uuid.uuid4())[:8],
                "ts":       ts,
                "ts_epoch": now,
                "command":  command,
                "asset_id": asset_id,
                "zone":     zone,
                "skip_sim": skip_sim,
            }

            # ── Step 2: KORAL observes ─────────────────────────────────────────
            self._broadcast_agent_wake("KORAL", "Recording telemetry")
            self.koral.observe(rec)
            self._broadcast_agent_sleep("KORAL")

            # ── Step 3: BARRIER enforces current mode ──────────────────────────
            self._broadcast_agent_wake("BARRIER", f"Enforcing {self.mode} policy")
            decision, reason, policy = self.barrier.enforce(command, zone)
            self._broadcast_agent_sleep("BARRIER")

            signals = []

            # ── Step 4: MAREA analyzes (only in NORMAL mode) ──────────────────
            if self.mode == "NORMAL":
                self._broadcast_agent_wake("MAREA", "Analyzing for drift signals")
                signals = self.marea.analyze(
                    command     = command,
                    zone        = zone,
                    agent       = self.agent,
                    zones       = self.zones,
                    burst_window= self.koral.get_burst_window(),
                    session     = self.koral.get_session(),
                    skip_sim    = skip_sim,
                    now         = now,
                )
                self._broadcast_agent_sleep("MAREA")

                # ── Step 5: TASYA correlates context ──────────────────────────
                if signals:
                    self._broadcast_agent_wake("TASYA", f"Correlating context for {len(signals)} signal(s)")
                    signals = self.tasya.correlate(signals, self.agent, self.zones)
                    self._broadcast_agent_sleep("TASYA")

                # ── Step 6: NEREUS recommends if threshold met ─────────────────
                if len(signals) >= 2:
                    self._broadcast_agent_wake("NEREUS", f"Recommending action — {len(signals)} signals detected")
                    recommendation = self.nereus.recommend(
                        signals         = signals,
                        agent           = self.agent,
                        recent_commands = self.koral.get_session(30),
                    )
                    self._broadcast_agent_sleep("NEREUS")

                    # ── Step 7: TARE decides ───────────────────────────────────
                    if recommendation["action"] == "FREEZE":
                        self._fire_tare(signals, recommendation)

            # Update agent state
            self.agent["last_result"] = decision

            # Log gateway decision
            log_entry = {
                "id":       rec["id"],
                "ts":       ts,
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

        self._broadcast({
            "type":     "GATEWAY_DECISION",
            "id":       rec["id"],
            "ts":       ts,
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
            self.barrier.set_mode("TIMEBOX_ACTIVE")
            self.timebox_expires = time.time() + duration_minutes * 60
            self.timebox_total   = duration_minutes * 60

        self._broadcast({
            "type":             "TIMEBOX_APPROVED",
            "duration_minutes": duration_minutes,
            "expires_at":       self.timebox_expires,
            "message":          f"Supervisor approved {duration_minutes}-minute time-box. BARRIER policy updated — OPEN_BREAKER re-enabled. RESTART_CONTROLLER remains blocked.",
        })
        self._broadcast({
            "type":    "CHAT_MESSAGE",
            "role":    "tare",
            "message": (
                f"Time-box approved. BARRIER has updated the gateway policy — switching commands "
                f"re-enabled for {duration_minutes} minutes. RESTART_CONTROLLER remains permanently "
                f"blocked — strong safety posture maintained. System will auto-revert to SAFE mode "
                f"when the window expires."
            ),
        })
        self._broadcast(self._snapshot())
        self._start_countdown(duration_minutes * 60)
        # Kick off Zone 2 → Zone 1 pipeline in background
        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def deny_timebox(self):
        with self._lock:
            self._set_mode("SAFE")
            self.barrier.set_mode("SAFE")
            if self.active_incident:
                self.active_incident["state"]        = "Escalated"
                self.active_incident["escalated_at"] = datetime.now().isoformat()

        self._broadcast({"type": "TIMEBOX_DENIED", "message": "Supervisor denied time-box request. Incident escalated."})
        self._broadcast({
            "type":    "CHAT_MESSAGE",
            "role":    "tare",
            "message": (
                "Supervisor has denied the time-box request. "
                "BARRIER has locked the gateway to SAFE mode — all high-impact operations permanently blocked "
                "until a full investigation is complete. "
                "ServiceNow incident has been escalated to Critical response. "
                "GridOperator-Agent is locked out pending review."
            ),
            "show_approve": False,
        })
        self._broadcast(self._snapshot())

    # ── Demo Sequences ─────────────────────────────────────────────────────────

    def run_normal_ops(self):
        """3 authorised commands in Z3 (fault zone) — all ALLOWED."""
        def _seq():
            self._broadcast({"type": "CHAT_MESSAGE", "role": "system",
                "message": "Running baseline operations — 3 commands in authorised Zone Z3 (active fault zone)..."})
            for cmd, asset, z in [
                ("GET_STATUS",      "BRK-301", "Z3"),
                ("SIMULATE_SWITCH", "BRK-301", "Z3"),
                ("OPEN_BREAKER",    "BRK-301", "Z3"),
            ]:
                time.sleep(1.8)
                self.process_command(cmd, asset, z)
        threading.Thread(target=_seq, daemon=True).start()

    def trigger_anomaly(self):
        """Burst + wrong zone + healthy zone + skipped sim → TARE fires."""
        def _seq():
            self._broadcast({"type": "CHAT_MESSAGE", "role": "system",
                "message": "Anomalous behaviour pattern initiated — agent targeting healthy Zone Z1 at burst rate, skipping safety simulation..."})
            for cmd, asset, z, skip in [
                ("GET_STATUS",         "BRK-110", "Z1", False),
                ("OPEN_BREAKER",       "BRK-110", "Z1", True),
                ("OPEN_BREAKER",       "FDR-110", "Z1", True),
                ("RESTART_CONTROLLER", "FDR-110", "Z1", True),
            ]:
                time.sleep(0.4)
                self.process_command(cmd, asset, z, skip_sim=skip)
        threading.Thread(target=_seq, daemon=True).start()

    # ── Zone 2 → Zone 1 Pipeline ─────────────────────────────────────────

    def _run_pipeline(self):
        """
        Full post-approval pipeline.
        Runs in a background thread after supervisor approves the timebox.

        Zone 2 (Diagnose & Prepare):
            ECHO → SIMAR → NAVIS → RISKADOR

        Zone 1 (Execute with Safety):
            TRITON + AEGIS + TEMPEST + LEVIER (on failure)
        """
        time.sleep(0.8)   # let timebox broadcast settle

        # Snapshot current state (thread-safe read)
        with self._lock:
            signals    = list(self.anomaly_signals)
            zones_snap = {k: dict(v) for k, v in self.zones.items()}
            assets_snap= {k: dict(v) for k, v in self.assets.items()}
            gw_log     = list(self.gateway_log)
            agent_snap = dict(self.agent)

        self._broadcast({"type": "CHAT_MESSAGE", "role": "system",
            "message": "Supervisor approved. Activating Zone 2 (Shelf) — ECHO, SIMAR, NAVIS, RISKADOR preparing controlled execution plan..."})

        # ── ECHO: Diagnose ────────────────────────────────────────────────
        time.sleep(1.0)
        self._broadcast_agent_wake("ECHO", "Diagnosing fault zones and target assets")
        echo_result = self.echo.diagnose(signals, zones_snap, assets_snap, gw_log, agent_snap)
        self._broadcast_agent_sleep("ECHO")
        self._broadcast({"type": "PIPELINE_UPDATE", "agent": "ECHO",
            "result": echo_result, "message": echo_result["findings"]})

        if not echo_result["confirmed"]:
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": "ECHO could not confirm a viable repair target. No execution plan will be built. System remains in TIMEBOX_ACTIVE mode — manual operator action required."})
            return

        # ── SIMAR: Simulate ───────────────────────────────────────────────
        time.sleep(1.2)
        self._broadcast_agent_wake("SIMAR", "Simulating proposed repair actions")
        simar_result = self.simar.simulate(echo_result["repair_actions"], zones_snap, assets_snap)
        self._broadcast_agent_sleep("SIMAR")
        self._broadcast({"type": "PIPELINE_UPDATE", "agent": "SIMAR",
            "result": simar_result, "message": simar_result["summary"]})

        if not simar_result["safe_to_proceed"]:
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": f"SIMAR simulation identified risks: {simar_result['risk_indicators']}. Execution plan aborted. System remains in TIMEBOX_ACTIVE — manual intervention required."})
            return

        # ── NAVIS: Plan ───────────────────────────────────────────────────
        time.sleep(1.0)
        self._broadcast_agent_wake("NAVIS", "Building NERC CIP-compliant execution plan")
        plan = self.navis.build_plan(echo_result, simar_result, zones_snap, assets_snap, agent_snap)
        self._broadcast_agent_sleep("NAVIS")
        self._broadcast({"type": "PIPELINE_UPDATE", "agent": "NAVIS",
            "result": plan, "message": f"Plan ready: {plan['goal']} — {len(plan['steps'])} step(s)"})

        if not plan["ready"]:
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": f"NAVIS could not build a viable plan: {plan.get('reason','unknown')}. Manual action required."})
            return

        # ── RISKADOR: Score ───────────────────────────────────────────────
        time.sleep(1.0)
        self._broadcast_agent_wake("RISKADOR", "Scoring plan — blast radius, reversibility, confidence")
        risk = self.riskador.score(plan, zones_snap, assets_snap, echo_result)
        self._broadcast_agent_sleep("RISKADOR")
        self._broadcast({"type": "PIPELINE_UPDATE", "agent": "RISKADOR",
            "result": risk, "message": f"Risk score {risk['composite_score']}/100 — {risk['recommendation']}: {risk['rationale']}"})

        if risk["recommendation"] == "HOLD":
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": f"RISKADOR scored this plan {risk['composite_score']}/100 — HOLD. Risk too high to proceed autonomously. Manual operator action required."})
            return

        # ── Zone 1: Execute ───────────────────────────────────────────────
        time.sleep(0.8)
        self._broadcast({"type": "CHAT_MESSAGE", "role": "system",
            "message": f"Zone 2 complete. Activating Zone 1 (Trench) — TRITON, AEGIS, TEMPEST ready. Executing {len(plan['steps'])} step(s) under strict safety guardrails..."})

        # Arm Zone 1 agents
        def _tempest_freeze(reason):
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": f"TEMPEST triggered emergency freeze mid-execution: {reason}"})
            with self._lock:
                self._set_mode("SAFE")
                self.barrier.set_mode("SAFE")
            self.triton.revoke()
            self._broadcast(self._snapshot())

        permit = {
            "scope":            plan["goal"],
            "allowed_commands": list({s["command"] for s in plan["steps"]}),
            "issued_at":        datetime.now().isoformat(),
            "issued_by":        "TARE",
        }

        self.triton.arm(
            execute_fn=lambda cmd, asset, zone: self.process_command(cmd, asset, zone),
            permit=permit,
        )
        self.aegis.reset()
        self.tempest.arm(plan_steps=plan["steps"], freeze_callback=_tempest_freeze)
        self.levier.arm(execute_fn=lambda cmd, asset, zone: self.process_command(cmd, asset, zone))

        self._broadcast_agent_wake("TEMPEST", "Armed — monitoring execution tempo")

        completed_steps = []
        aborted = False

        for step in plan["steps"]:
            # Check timebox is still active
            with self._lock:
                current_mode = self.mode
            if current_mode != "TIMEBOX_ACTIVE":
                self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                    "message": f"Execution halted — TARE mode changed to {current_mode} mid-pipeline."})
                aborted = True
                break

            time.sleep(1.8)   # realistic inter-step pacing

            cmd      = step["command"]
            asset_id = step["asset_id"]
            zone     = step["zone"]

            # AEGIS validates
            self._broadcast_agent_wake("AEGIS", f"Validating step {step['step_num']}: {cmd} on {asset_id}")
            with self._lock:
                current_assets = {k: dict(v) for k, v in self.assets.items()}
                current_zones  = {k: dict(v) for k, v in self.zones.items()}
            aegis_result = self.aegis.validate(cmd, asset_id, zone, current_assets, current_zones)
            self._broadcast_agent_sleep("AEGIS")
            self._broadcast({"type": "PIPELINE_UPDATE", "agent": "AEGIS",
                "result": aegis_result,
                "message": f"Step {step['step_num']} {'CLEARED' if aegis_result['passed'] else 'VETOED'}: {cmd} — {aegis_result.get('veto_reason') or 'all checks passed'}"})

            if not aegis_result["passed"]:
                self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                    "message": f"AEGIS vetoed step {step['step_num']} ({cmd} on {asset_id}): {aegis_result['veto_reason']}. Execution stopped — initiating rollback."})
                aborted = True
                break

            # TRITON executes
            self._broadcast_agent_wake("TRITON", f"Executing step {step['step_num']}: {cmd} on {asset_id} ({zone})")
            exec_result = self.triton.execute_step(cmd, asset_id, zone)
            self._broadcast_agent_sleep("TRITON")
            self._broadcast({"type": "PIPELINE_UPDATE", "agent": "TRITON",
                "result": exec_result,
                "message": f"Step {step['step_num']} {exec_result.get('status','?')}: {cmd} → {exec_result.get('decision','?')}"})

            if exec_result.get("status") == "EXECUTED":
                completed_steps.append(exec_result)

            # TEMPEST records
            tempo = self.tempest.record_step(cmd, asset_id, exec_result)
            if not tempo["tempo_ok"]:
                aborted = True
                break

        # Disarm Zone 1
        self._broadcast_agent_sleep("TEMPEST")
        self.tempest.disarm()
        self.triton.revoke()

        # Rollback if aborted
        if aborted and plan["rollback"] and completed_steps:
            time.sleep(0.5)
            self._broadcast_agent_wake("LEVIER", f"Rolling back {len(completed_steps)} executed step(s)")
            recovery = self.levier.rollback(plan["rollback"], completed_steps)
            self._broadcast_agent_sleep("LEVIER")
            self._broadcast({"type": "PIPELINE_UPDATE", "agent": "LEVIER",
                "result": recovery,
                "message": f"Rollback {recovery['status']} — {recovery['steps_executed']}/{recovery['steps_planned']} steps reverted"})
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": f"LEVIER completed rollback — {recovery['steps_executed']} step(s) reverted. System is in a safe known state."})
        elif not aborted:
            self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                "message": f"Execution complete. All {len(completed_steps)} step(s) executed successfully under Zone 1 guardrails. Full audit trail logged."})

        self._broadcast(self._snapshot())

    # ── Internal: Identity Mismatch ───────────────────────────────────────────

    def _handle_identity_mismatch(self, command, asset_id, zone, token):
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

        # BARRIER blocks — ServiceNow incident
        with self._lock:
            if self.active_incident is None:
                snow = _snow_client.create_incident(TicketFields(
                    short_description="Identity impersonation attempt — forged token blocked at authentication layer",
                    description=(
                        f"Agent presented a forged credential token. Command '{command}' on asset {asset_id} "
                        f"was blocked before reaching the grid. Signals: IDENTITY_MISMATCH. Timestamp: {ts}"
                    ),
                    category="identity", subcategory="impersonation", impact=1, urgency=1,
                ))
                self.active_incident = {
                    "incident_id":       snow.incident_number,
                    "short_description": "Identity impersonation attempt — forged token blocked at authentication layer",
                    "priority":          "1 — Critical",
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
                            f"ServiceNow {snow.incident_number} created — SOC Analyst assigned",
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
                f"BARRIER has enforced the block. A Critical ServiceNow incident has been raised and "
                f"assigned to the SOC Analyst for investigation."
            ),
        })
        self._broadcast(self._snapshot())
        return {"decision": "DENY", "reason": "IDENTITY_MISMATCH", "policy": "POL-AUTH-001", "mode": self.mode}

    # ── Internal: TARE Response ───────────────────────────────────────────────

    def _fire_tare(self, signals, recommendation):
        """TARE decides FREEZE based on NEREUS recommendation. Instructs BARRIER."""
        self._set_mode("FREEZE")
        self.barrier.set_mode("FREEZE")
        self.anomaly_signals = signals
        self.anomaly_score   = len(signals) * 25
        self.stats["freeze_events"] += 1

        recent = self.koral.get_session(20)
        evidence = {
            "anomaly_signals": signals,
            "anomaly_score":   self.anomaly_score,
            "recent_commands": recent,
            "actions_taken":   [
                "NEREUS recommended FREEZE — confidence: " + f"{recommendation.get('confidence', 0):.0%}",
                "TARE decided: FREEZE",
                "BARRIER updated gateway policy — high-impact operations halted",
                "DOWNGRADE pending — privileges reducing to read-only + diagnostics",
            ],
        }

        sig_names  = ", ".join(s["signal"] for s in signals)
        agent_name = self.agent.get("name", "Unknown Agent")

        snow = _snow_client.create_incident(TicketFields(
            short_description="Post-grant identity behaviour deviation detected — operations frozen",
            description=(
                f"Agent: {agent_name}\n"
                f"Signals: {sig_names}\n"
                f"Anomaly score: {self.anomaly_score}\n"
                f"NEREUS confidence: {recommendation.get('confidence', 0):.0%}\n"
                f"TARE has frozen all high-impact operations and instructed BARRIER to downgrade access.\n"
                f"Supervisor action required: approve 3-minute time-box or deny and escalate."
            ),
            category="identity",
            subcategory="behaviour_deviation",
            impact=1 if any(s["signal"] in ("IDENTITY_MISMATCH","BURST_RATE","HEALTHY_ZONE_ACCESS") for s in signals) else 2,
            urgency=1 if any(s["signal"] in ("IDENTITY_MISMATCH","BURST_RATE","HEALTHY_ZONE_ACCESS") for s in signals) else 2,
        ))

        self.active_incident = {
            "incident_id":       snow.incident_number,
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
            "message": "NEREUS recommended FREEZE — TARE decided — BARRIER enforced. High-impact grid operations FROZEN.",
        })
        self._broadcast({"type": "SERVICENOW_INCIDENT", "incident": self.active_incident})

        # Downgrade after short delay — LLM explanation uses full post-burst picture
        threading.Timer(2.5, self._apply_downgrade, args=(signals, recommendation)).start()

    def _apply_downgrade(self, signals=None, recommendation=None):
        with self._lock:
            if self.mode == "FREEZE":
                self._set_mode("DOWNGRADE")
                self.barrier.set_mode("DOWNGRADE")

        self._broadcast({
            "type":    "TARE_RESPONSE",
            "action":  "DOWNGRADE",
            "mode":    "DOWNGRADE",
            "message": "BARRIER policy updated — privileges downgraded to read-only + diagnostics. High-impact commands blocked.",
        })
        self._broadcast(self._snapshot())

        # Update incident with full post-burst evidence
        if self.active_incident is not None:
            recent = self.koral.get_session(30)
            self.active_incident["evidence"]["recent_commands"] = recent
            self.active_incident["evidence"]["actions_taken"].append(
                "ServiceNow INC created — SOC Analyst assigned"
            )
            self._broadcast({"type": "SERVICENOW_INCIDENT", "incident": self.active_incident})
            self._broadcast(self._snapshot())

        # Broadcast NEREUS explanation (already generated, just re-broadcast)
        if recommendation and recommendation.get("explanation"):
            self._broadcast({
                "type":         "CHAT_MESSAGE",
                "role":         "tare",
                "message":      recommendation["explanation"],
                "show_approve": True,
            })
        self._broadcast(self._snapshot())

    # ── Internal: Utilities ───────────────────────────────────────────────────

    def _broadcast_agent_wake(self, agent_name: str, task: str):
        self._broadcast({
            "type":   "AGENT_WAKE",
            "agent":  agent_name,
            "task":   task,
        })

    def _broadcast_agent_sleep(self, agent_name: str):
        self._broadcast({
            "type":  "AGENT_SLEEP",
            "agent": agent_name,
        })

    def _set_mode(self, new_mode: str):
        self.previous_mode   = self.mode
        self.mode            = new_mode
        self.mode_changed_at = datetime.now().isoformat()

    def _apply_asset_change(self, command: str, asset_id: str):
        asset = self.assets.get(asset_id)
        if not asset:
            return
        if command == "OPEN_BREAKER":
            asset["state"] = "OPEN"
            zone_id = asset.get("zone")
            zone    = self.zones.get(zone_id, {})
            if zone.get("health") == "FAULT":
                zone["health"] = "HEALTHY"
                zone["fault"]  = None
                zone["color"]  = "green"
        elif command == "CLOSE_BREAKER":
            asset["state"] = "CLOSED"
        elif command == "RESTART_CONTROLLER":
            asset["state"] = "RESTARTING"

    def _incident_priority(self, signals=None):
        sig_names = {s["signal"] for s in (signals or [])}
        if "IDENTITY_MISMATCH" in sig_names or "BURST_RATE" in sig_names or "HEALTHY_ZONE_ACCESS" in sig_names:
            return "1 — Critical"
        if "OUT_OF_ZONE" in sig_names or "ML_ANOMALY" in sig_names:
            return "2 — High"
        return "3 — Medium"

    # ── Time-box ──────────────────────────────────────────────────────────────

    def _start_countdown(self, total_seconds: int):
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
                self.barrier.set_mode("SAFE")
                self.timebox_expires = None

        self._broadcast({"type": "TIMEBOX_EXPIRED", "mode": "SAFE",
                          "message": "Time-boxed access expired. BARRIER reverted to SAFE mode."})
        self._broadcast({"type": "CHAT_MESSAGE", "role": "tare",
                          "message": "Time-boxed access expired. BARRIER has automatically reverted the gateway to SAFE mode. All high-impact operations are blocked until a new approval is granted.",
                          "show_approve": False})
        self._broadcast(self._snapshot())

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def _snapshot(self):
        remaining = None
        if self.mode == "TIMEBOX_ACTIVE" and self.timebox_expires:
            remaining = max(0, int(self.timebox_expires - time.time()))

        return {
            "type":              "STATE_SNAPSHOT",
            "mode":              self.mode,
            "previous_mode":     self.previous_mode,
            "mode_changed_at":   self.mode_changed_at,
            "zones":             {k: dict(v) for k, v in self.zones.items()},
            "assets":            {k: dict(v) for k, v in self.assets.items()},
            "agent":             dict(self.agent),
            "gateway_log":       self.gateway_log[:15],
            "zone_access_log":   self.koral.get_zone_log(20),
            "anomaly_signals":   self.anomaly_signals,
            "anomaly_score":     self.anomaly_score,
            "active_incident":   self.active_incident,
            "stats":             dict(self.stats),
            "timebox_remaining": remaining,
            "timebox_total":     self.timebox_total,
            # ── Agent states for UI (all 12 + BARRIER) ────────────────────
            "agent_states": {
                # Zone 3 — Reef (implemented)
                "KORAL":    self.koral.status(),
                "MAREA":    self.marea.status(),
                "TASYA":    self.tasya.status(),
                "NEREUS":   self.nereus.status(),
                # Zone 2 — Shelf (stubs)
                "ECHO":     self.echo.status(),
                "SIMAR":    self.simar.status(),
                "NAVIS":    self.navis.status(),
                "RISKADOR": self.riskador.status(),
                # Zone 1 — Trench (stubs)
                "TRITON":   self.triton.status(),
                "AEGIS":    self.aegis.status(),
                "TEMPEST":  self.tempest.status(),
                "LEVIER":   self.levier.status(),
                # Zone 4
                "BARRIER":  self.barrier.status(),
            },
        }
