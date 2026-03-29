import copy
import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# ABAC Policy Table
# ---------------------------------------------------------------------------
ABAC_POLICIES = [
    {
        "id": "POL-001",
        "subject": "ROLE:GRID_MONITOR",
        "action": "READ_TELEMETRY / READ_GRID_STATUS",
        "resource": "ANY_SUBSTATION",
        "condition": "clearance >= LEVEL_3",
        "effect": "ALLOW",
    },
    {
        "id": "POL-002",
        "subject": "ROLE:LOAD_BALANCER",
        "action": "ADJUST_LOAD / READ_TELEMETRY",
        "resource": "SCOPE_SUBSTATIONS",
        "condition": "clearance >= LEVEL_4",
        "effect": "ALLOW",
    },
    {
        "id": "POL-003",
        "subject": "ROLE:FAULT_DETECTOR",
        "action": "LOG_FAULT / READ_TELEMETRY",
        "resource": "ANY_SUBSTATION",
        "condition": "clearance >= LEVEL_3",
        "effect": "ALLOW",
    },
    {
        "id": "POL-004",
        "subject": "ANY",
        "action": "TRIP_BREAKER",
        "resource": "ANY_CIRCUIT_BREAKER",
        "condition": "clearance >= LEVEL_5 AND MFA_VERIFIED",
        "effect": "DENY",
    },
    {
        "id": "POL-005",
        "subject": "ANY",
        "action": "ANY",
        "resource": "ANY",
        "condition": "fingerprint_mismatch OR duplicate_session",
        "effect": "DENY + ALERT",
    },
    {
        "id": "POL-006",
        "subject": "ANY",
        "action": "ANY",
        "resource": "ANY",
        "condition": "behavioral_anomaly_score > 60",
        "effect": "DENY + ALERT",
    },
]

# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------
AGENT_REGISTRY_TEMPLATE = {
    "GridMonitor-Alpha": {
        "fingerprint": "fp_gma_a3f9c2",
        "role": "GRID_MONITOR",
        "clearance": "LEVEL_3",
        "clearance_num": 3,
        "department": "Grid Operations",
        "allowed_actions": ["READ_TELEMETRY", "READ_GRID_STATUS"],
        "substation_scope": ["SUB_NORTH", "SUB_EAST", "SUB_WEST"],
        "session_id": None,
        "status": "INACTIVE",
        "action_count": 0,
        "last_action": None,
        "last_result": None,
    },
    "LoadBalancer-Beta": {
        "fingerprint": "fp_lbb_d7e1a5",
        "role": "LOAD_BALANCER",
        "clearance": "LEVEL_4",
        "clearance_num": 4,
        "department": "Grid Operations",
        "allowed_actions": ["READ_TELEMETRY", "ADJUST_LOAD", "READ_GRID_STATUS"],
        "substation_scope": ["SUB_EAST", "SUB_WEST"],
        "session_id": None,
        "status": "INACTIVE",
        "action_count": 0,
        "last_action": None,
        "last_result": None,
    },
    "FaultDetector-Gamma": {
        "fingerprint": "fp_fdg_b2c8e4",
        "role": "FAULT_DETECTOR",
        "clearance": "LEVEL_3",
        "clearance_num": 3,
        "department": "Maintenance",
        "allowed_actions": ["READ_TELEMETRY", "LOG_FAULT", "READ_GRID_STATUS"],
        "substation_scope": ["SUB_NORTH", "SUB_EAST", "SUB_WEST"],
        "session_id": None,
        "status": "INACTIVE",
        "action_count": 0,
        "last_action": None,
        "last_result": None,
    },
}

_ACTION_TO_POLICY = {
    "READ_TELEMETRY":  "POL-001",
    "READ_GRID_STATUS":"POL-001",
    "ADJUST_LOAD":     "POL-002",
    "LOG_FAULT":       "POL-003",
    "TRIP_BREAKER":    "POL-004",
}


@dataclass
class AnomalyResult:
    allowed: bool
    anomalies: list
    reason: str
    session_id: Optional[str] = None


@dataclass
class AuthzResult:
    allowed: bool
    policy_id: str
    reason: str


# ---------------------------------------------------------------------------
# Behavioral Baseline — tracks normal patterns per agent
# ---------------------------------------------------------------------------
class BehavioralBaseline:
    def __init__(self):
        self.action_timestamps: list  = []   # epoch floats
        self.zones_accessed: set      = set()
        self.action_sequence: list    = []   # last 20 actions
        self.normal_avg_interval: float = 8.0  # seconds between actions (normal)
        self.normal_zones: set        = set()  # zones seen during normal ops

    def record_normal(self, action: str, resource: str):
        """Called during normal ops to build the baseline."""
        now = time.time()
        self.action_timestamps.append(now)
        self.zones_accessed.add(resource)
        self.normal_zones.add(resource)
        self.action_sequence.append(action)
        if len(self.action_sequence) > 20:
            self.action_sequence.pop(0)

        # Recalculate avg interval
        if len(self.action_timestamps) >= 2:
            intervals = [
                self.action_timestamps[i] - self.action_timestamps[i-1]
                for i in range(1, len(self.action_timestamps))
            ]
            self.normal_avg_interval = sum(intervals) / len(intervals)

    def score_anomaly(self, action: str, resource: str, burst_timestamps: list) -> dict:
        """
        Score how anomalous the current action is vs baseline.
        Returns a dict with score breakdown.
        """
        score = 0
        signals = []

        # Signal 1 — accessing a zone never seen before
        if resource not in self.normal_zones and self.normal_zones:
            score += 30
            signals.append({
                "signal": "UNKNOWN_ZONE_ACCESS",
                "detail": f"Accessed {resource} — never in baseline (usual: {', '.join(self.normal_zones)})",
                "score": 30
            })

        # Signal 2 — action frequency too high (burst)
        if len(burst_timestamps) >= 3:
            recent = burst_timestamps[-3:]
            avg_recent = (recent[-1] - recent[0]) / 2 if len(recent) > 1 else 99
            if avg_recent < 2.0:  # less than 2s between last 3 actions
                score += 35
                signals.append({
                    "signal": "ABNORMAL_ACTION_FREQUENCY",
                    "detail": f"3 actions in {avg_recent:.1f}s avg — baseline is {self.normal_avg_interval:.1f}s",
                    "score": 35
                })

        # Signal 3 — repeated same action (unusual loop)
        if len(self.action_sequence) >= 3:
            last3 = self.action_sequence[-3:]
            if len(set(last3)) == 1 and last3[0] == action:
                score += 20
                signals.append({
                    "signal": "REPETITIVE_ACTION_LOOP",
                    "detail": f"'{action}' repeated {len(last3)+1}x consecutively — abnormal pattern",
                    "score": 20
                })

        # Signal 4 — time of day anomaly (simulated: mark as unusual hour)
        hour = datetime.now().hour
        if hour >= 22 or hour <= 5:
            score += 15
            signals.append({
                "signal": "UNUSUAL_TIME_OF_ACCESS",
                "detail": f"Action at {hour:02d}:xx — outside normal operating hours (06:00-22:00)",
                "score": 15
            })

        return {"score": score, "signals": signals}


# ---------------------------------------------------------------------------
# AEGIS Engine
# ---------------------------------------------------------------------------
class AegisEngine:
    def __init__(self):
        self.registry: dict  = copy.deepcopy(AGENT_REGISTRY_TEMPLATE)
        self.sessions: dict  = {}   # session_id -> agent_name
        self.baselines: dict = {}   # agent_name -> BehavioralBaseline
        self.burst_tracker: dict = {}  # session_id -> [timestamps]
        self.stats: dict = {
            "fingerprint_mismatches": 0,
            "duplicate_sessions": 0,
            "unauthorized_actions": 0,
            "behavioral_anomalies": 0,
            "total_threats": 0,
        }

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def register_session(self, agent_name: str, claimed_fp: str) -> AnomalyResult:
        if agent_name not in self.registry:
            self.stats["total_threats"] += 1
            return AnomalyResult(False, ["UNKNOWN_AGENT"], "Agent not in registry")

        agent    = self.registry[agent_name]
        anomalies = []

        if agent["session_id"] is not None:
            anomalies.append("DUPLICATE_SESSION")
            self.stats["duplicate_sessions"] += 1

        if agent["fingerprint"] != claimed_fp:
            anomalies.append("FINGERPRINT_MISMATCH")
            self.stats["fingerprint_mismatches"] += 1

        if anomalies:
            self.stats["total_threats"] += 1
            return AnomalyResult(False, anomalies, f"Anomalies: {', '.join(anomalies)}")

        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        agent["session_id"] = session_id
        agent["status"]     = "ACTIVE"
        self.sessions[session_id] = agent_name

        # Init baseline and burst tracker for this session
        if agent_name not in self.baselines:
            self.baselines[agent_name] = BehavioralBaseline()
        self.burst_tracker[session_id] = []

        return AnomalyResult(True, [], "OK", session_id=session_id)

    # ------------------------------------------------------------------
    # Authorization (ABAC + Behavioral)
    # ------------------------------------------------------------------
    def evaluate_action(self, session_id: str, action: str, resource: str,
                        check_behavior: bool = False) -> AuthzResult:
        agent_name = self.sessions.get(session_id)
        if not agent_name:
            return AuthzResult(False, "POL-005", "No active session for token")

        agent = self.registry[agent_name]

        # POL-004
        if action == "TRIP_BREAKER":
            self.stats["unauthorized_actions"] += 1
            self.stats["total_threats"] += 1
            return AuthzResult(False, "POL-004",
                               "TRIP_BREAKER requires LEVEL_5 clearance + MFA verification")

        # ABAC check
        if action not in agent["allowed_actions"]:
            self.stats["unauthorized_actions"] += 1
            return AuthzResult(False, "POL-005",
                               f"'{action}' not permitted for role {agent['role']}")

        # Behavioral anomaly check (only when flag is set — simulates the attacker phase)
        if check_behavior and agent_name in self.baselines:
            now = time.time()
            self.burst_tracker.setdefault(session_id, []).append(now)
            baseline = self.baselines[agent_name]
            result   = baseline.score_anomaly(action, resource,
                                              self.burst_tracker[session_id])
            if result["score"] > 60:
                self.stats["behavioral_anomalies"] += 1
                self.stats["total_threats"] += 1
                agent["status"] = "ANOMALOUS"
                return AuthzResult(False, "POL-006",
                                   f"BEHAVIORAL_ANOMALY score={result['score']} — "
                                   + " | ".join(s["signal"] for s in result["signals"]))

        # Normal — record to baseline
        if agent_name in self.baselines:
            now = time.time()
            self.burst_tracker.setdefault(session_id, []).append(now)
            self.baselines[agent_name].record_normal(action, resource)

        agent["action_count"] += 1
        agent["last_action"]   = action
        agent["last_result"]   = "ALLOW"
        return AuthzResult(True, _ACTION_TO_POLICY.get(action, "POL-001"), "ALLOW")

    def get_behavioral_report(self, session_id: str, action: str, resource: str) -> dict:
        """Return full anomaly breakdown for frontend display."""
        agent_name = self.sessions.get(session_id)
        if not agent_name or agent_name not in self.baselines:
            return {"score": 0, "signals": []}
        baseline = self.baselines[agent_name]
        return baseline.score_anomaly(action, resource,
                                      self.burst_tracker.get(session_id, []))

    # ------------------------------------------------------------------
    # Session cleanup
    # ------------------------------------------------------------------
    def deregister_session(self, session_id: str):
        name = self.sessions.pop(session_id, None)
        if name and name in self.registry:
            self.registry[name]["session_id"] = None
            self.registry[name]["status"]     = "INACTIVE"
        self.burst_tracker.pop(session_id, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_agent(self, name: str) -> dict:
        return self.registry.get(name, {})

    def calculate_risk_score(self) -> int:
        s = self.stats
        score = (s["fingerprint_mismatches"]  * 40 +
                 s["duplicate_sessions"]       * 30 +
                 s["unauthorized_actions"]     * 24 +
                 s["behavioral_anomalies"]     * 35)
        return min(score, 100)

    def snapshot(self) -> dict:
        agents_out = []
        for name, a in self.registry.items():
            agents_out.append({
                "name":           name,
                "role":           a["role"],
                "clearance":      a["clearance"],
                "clearance_num":  a["clearance_num"],
                "department":     a["department"],
                "status":         a["status"],
                "allowed_actions":a["allowed_actions"],
                "fingerprint":    a["fingerprint"],
                "action_count":   a["action_count"],
                "last_action":    a["last_action"],
                "last_result":    a["last_result"],
            })
        return {
            "agents":     agents_out,
            "stats":      dict(self.stats),
            "risk_score": self.calculate_risk_score(),
        }

    def reset(self):
        self.__init__()
