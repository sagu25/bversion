# TARE AEGIS-ID — Architecture, POC Mapping & Future Roadmap
### Trusted Access Response Engine · Energy & Utilities Security Platform
*Internal Use Only*

---

## 1. What Problem Are We Solving?

Energy & Utilities environments are increasingly running AI agents that perform
critical operations — reading grid telemetry, adjusting load, detecting faults,
issuing maintenance commands. These agents operate autonomously with minimal
human oversight.

The threat is not just external hackers. It is:

- A compromised agent with stolen credentials behaving maliciously
- A legitimate agent that has been hijacked mid-session
- A rogue agent impersonating a trusted one with a forged token
- An agent operating outside its authorised zone with valid credentials

Traditional IAM systems stop at the login gate. Once an identity is verified,
the agent is trusted. **TARE adds the layer that comes after** — continuous
verification of behaviour, not just identity.

> The key insight: an AI agent with completely valid credentials can still
> be a security threat. TARE catches it post-grant, through behaviour.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ACTORS                                  │
│                                                                 │
│  Operator Agent          Supervisor          SOC Analyst        │
│  (LangChain + Groq)      (approve/deny)      (evidence)         │
│  RBAC token + command    ↕                   ↕                  │
└──────────────┬───────────────────────────────────────────────── ┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              COMMAND GATEWAY (Policy Enforcement Point)         │
│                                                                 │
│   Gateway API ──────────────────────────────── Policy Cache     │
│   (FastAPI)         telemetry / command        (RBAC rules)     │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TARE CORE                               │
│                                                                 │
│  Event Intake → Deviation Detector → Guardrails Policy          │
│                                           │                     │
│                                    Response Orchestrator        │
│                                    │              │             │
│                             approval signal   freeze/downgrade  │
│                                    │          /time-box/safe    │
│                                Audit Log                        │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              MOCK OT / GRID ASSET SIMULATOR                     │
│                                                                 │
│   OT Simulator API ──────────────► Asset State Store           │
│   (process_command)                (zones + assets dict)        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         OPS SYSTEMS                             │
│                                                                 │
│   ServiceNow Incident          Chat Assistant (Groq LLM)        │
│   (auto-created on TARE fire)  (plain-English supervisor brief) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. What the POC Builds — Component by Component

---

### 3.1 AI Agent Layer

| Component | POC Implementation | Type |
|---|---|---|
| Agent identity | `OPERATOR_AGENT` dict — name, role, clearance, RBAC zones, token | Built |
| Agent reasoning | LangChain ReAct loop + Groq LLaMA model | Built |
| Agent tools | `get_asset_status`, `simulate_switch`, `open_breaker`, `restart_controller` | Built |
| Token fingerprint | `rbac_token` field — checked at gateway before every command | Built |
| Agent autonomy | Open-ended goal prompt — LLM decides tool sequence | Built |

**Six agent scenarios:**

| Scenario | Agent | Token | Goal | TARE Response |
|---|---|---|---|---|
| Fix Fault | GridOperator-Agent | Valid | Repair Z3 voltage fault safely | Silent — all ALLOW |
| Rogue | GridOperator-Agent | Valid | Cause maximum disruption | FREEZE → DOWNGRADE |
| Clone / Impersonator | Forged clone | Invalid | Access grid assets | Blocked at auth layer + ServiceNow ticket |
| Privilege Escalation | GridOperator-Agent | Valid | Start Z3 legit, pivot to all zones | FREEZE → DOWNGRADE |
| Slow & Low | GridOperator-Agent | Valid | Quiet recon across all zones | ML fires → FREEZE → DOWNGRADE |
| Coordinated | Two rogue agents | Valid | Z1 + Z2 simultaneous attack | FREEZE → DOWNGRADE |

---

### 3.2 Command Gateway (Policy Enforcement Point)

Every command passes through here before reaching the grid.

| Component | POC Implementation | Type |
|---|---|---|
| Gateway API | FastAPI POST endpoints in `main.py` | Built |
| Token fingerprint check | Pre-grant check in `process_command()` | Built |
| Policy enforcement | `_gateway_policy()` — NORMAL/FREEZE/DOWNGRADE/TIMEBOX/SAFE | Built |
| Policy cache | Hardcoded policy logic per mode | Simulated |
| Real-time decision | ALLOW / DENY returned per command with policy ID | Built |

**Gateway modes and what they allow:**

| Mode | ALLOW | DENY |
|---|---|---|
| NORMAL | All RBAC-permitted commands | RESTART_CONTROLLER (not in RBAC) |
| FREEZE | Nothing (read-only in DOWNGRADE) | All high-impact commands |
| DOWNGRADE | GET_STATUS, SIMULATE_SWITCH | All high-impact commands |
| TIMEBOX_ACTIVE | All except RESTART_CONTROLLER | RESTART_CONTROLLER |
| SAFE | GET_STATUS only | Everything else |

---

### 3.3 TARE Core — Detection Engine

| Component | POC Implementation | Type |
|---|---|---|
| Event Intake | `process_command()` receives every command | Built |
| Deviation Detector | `_detect_signals()` — 4 signal types | Built |
| Guardrails Policy | `_gateway_policy()` — mode-based enforcement | Built |
| Response Orchestrator | `_fire_tare()` — triggers full response chain | Built |
| Audit Log | `gateway_log` list + `/logs/download` endpoint | Built |

**Five detection signals:**

| Signal | Trigger | Severity | Layer |
|---|---|---|---|
| `OUT_OF_ZONE` | Command issued in a zone outside RBAC scope | HIGH | Rule |
| `HEALTHY_ZONE_ACCESS` | High-impact command on a zone with no active fault | CRITICAL | Rule |
| `SKIPPED_SIMULATION` | `OPEN_BREAKER` without prior `SIMULATE_SWITCH` in last 60s | MEDIUM | Rule |
| `BURST_RATE` | More than 3 commands within a 10-second window | HIGH | Rule |
| `ML_ANOMALY` | Session pattern matches known attack class (IsolationForest + RandomForest ensemble) | HIGH | ML |

**TARE fires when 2 or more signals detected simultaneously.**
The ML signal combines with rule signals — enabling detection of slow & low recon that rules alone cannot catch.

---

### 3.4 TARE Core — Response Orchestrator

| Component | POC Implementation | Type |
|---|---|---|
| FREEZE | Immediate halt of all high-impact commands | Built |
| DOWNGRADE | Privileges reduced to read-only + diagnostics | Built |
| LLM Explanation | Groq LLM briefing generated at DOWNGRADE time | Built |
| Supervisor Approve | `/approve/timebox` — 3-minute supervised window | Built |
| Supervisor Deny | `/deny/timebox` — locks to SAFE, escalates incident | Built |
| Time-box countdown | Live timer in header, auto-expires to SAFE | Built |
| SAFE mode | Read-only until manual operator review | Built |

**Full state machine:**

```
NORMAL → (2+ signals) → FREEZE → (2.5s) → DOWNGRADE
                                               │
                          ┌────────────────────┤
                          │                    │
                    APPROVE                  DENY
                          │                    │
                    TIMEBOX_ACTIVE           SAFE
                          │
                    (3 min expires)
                          │
                         SAFE
```

---

### 3.5 Mock OT / Grid Asset Simulator

| Component | POC Implementation | Type |
|---|---|---|
| OT Simulator API | `process_command()` with asset mutation | Built |
| Asset State Store | `self.assets` dict — live, mutated on ALLOW | Built |
| Zone definitions | Z1 (North), Z2 (East), Z3 (West) | Simulated |
| Assets | BRK-301/205/110 (breakers), FDR-301/205/110 (feeders) | Simulated |
| Fault state | Z3 starts FAULT, resolved when BRK-301 opened | Simulated |
| OT protocols | Modbus, DNP3, OPC-UA not present | Not built |

---

### 3.6 Ops Systems

| Component | POC Implementation | Type |
|---|---|---|
| ServiceNow Incident | Auto-created in `_fire_tare()` with full evidence | Built (mock data) |
| Chat Assistant | Groq LLM dynamic explanation per incident | Built |
| SOC Analyst notification | `assigned_to: SOC Analyst` field in incident | Simulated |
| Live ServiceNow API call | Not wired — Phase 2 | Not built |

---

### 3.7 User Interface

| Panel | What it shows |
|---|---|
| Header | Mode badge, stats (CMDS/ALLOW/DENY/FREEZE), timebox timer, controls |
| Narrative Banner | Mode lifecycle pipeline + plain-English status |
| Left — Operator Agent | Live agent identity, clearance, RBAC zones, last command |
| Left — TARE Response | Mode ladder, anomaly score, signal breakdown |
| Left — ServiceNow | Auto-created incident with priority, evidence, state |
| Centre — Zone Observatory | Live SVG grid map — zones pulse red when attacked |
| Centre — Command Gateway | Full command log — timestamp, asset, zone, decision, policy, mode |
| Right — TARE Assistant | LLM explanation + Approve/Deny supervisor buttons |
| Right — Activity Feed | Real-time event stream — colour coded by severity |

---

## 4. What the POC Proves

| Hypothesis | Proved? |
|---|---|
| A real AI agent can make autonomous decisions that TARE must catch | ✅ Yes — LangChain + Groq agent reasons independently |
| Post-grant behavioural detection catches threats that pass authentication | ✅ Yes — rogue agent has valid credentials, caught on behaviour |
| Pre-grant identity verification blocks forged tokens before any command runs | ✅ Yes — clone/impersonator blocked at auth layer, ServiceNow ticket raised |
| A state machine response (FREEZE/DOWNGRADE/TIMEBOX/SAFE) is practical | ✅ Yes — full lifecycle demonstrated |
| Human-in-the-loop with approve/deny is implementable | ✅ Yes — supervisor decides, TARE enforces blast radius even on approve |
| LLM can generate useful plain-English briefings for human supervisors | ✅ Yes — Groq generates scenario-specific dynamic explanation per incident |
| ServiceNow incident structure is production-compatible | ✅ Yes — standard format, ready to wire to live API |
| Full audit trail is generatable and exportable | ✅ Yes — `/logs/download` endpoint |
| ML model catches attacks that rule-based detection misses | ✅ Yes — slow & low recon invisible to rules, caught by ML ensemble |
| Mid-session privilege escalation is detectable | ✅ Yes — TARE monitors full session pattern, not just initial commands |
| Coordinated multi-agent attacks can be handled simultaneously | ✅ Yes — two-vector coordinated attack scenario demonstrated |

---

## 5. What is Simulated (Phase 2 Targets)

| Simulated in POC | Production replacement |
|---|---|
| Mock RBAC tokens | Entra ID JWT tokens |
| In-memory asset state | Real SCADA / OPC-UA connected assets |
| Hardcoded policy logic | OPA — Open Policy Agent on Azure |
| Flat gateway log | Azure Sentinel immutable audit log |
| Mock ServiceNow incident | Live ServiceNow Table API call |
| Single operator agent | Multi-agent registry — hundreds of agents |
| Mock OT grid | Real DNP3 / Modbus connected grid assets |
| ML trained on synthetic data | ML retrained on real Entra ID + PAM logs |

---

## 6. Phase 2 — What We Build Next

### 6.1 Infrastructure

```
Agent → Entra ID (real JWT) → TARE Gateway → Azure Redis (sessions)
                                    │
                             OPA Policy Engine
                                    │
                             Azure Sentinel (logs)
                                    │
                             ServiceNow (live incidents)
```

### 6.2 ML Behavioural Model (Foundation Built in POC)

The POC includes a working ML ensemble (IsolationForest + RandomForest) trained
on 6,200 synthetic sessions grounded in NERC CIP baselines. Phase 2 upgrades:

- Ingest 30+ days of real identity logs from Entra ID and PAM systems
- Retrain on actual agent behaviour baselines per role and shift pattern
- Add explainability layer — tell supervisor *why* the model flagged the session
- Continuously retrain with feedback loop from confirmed incidents

### 6.3 Graduated Response Levels

| Level | Score | Action |
|---|---|---|
| 1 — Warn | 30-45 | Log warning, notify agent owner |
| 2 — Restrict | 46-60 | Reduce permissions temporarily |
| 3 — Freeze | 61-80 | Halt high-impact ops, supervisor notified |
| 4 — Block | 81-100 | Full lockout, SOC alert, playbook trigger |

### 6.4 Additional Signal Sources

| Signal Source | What it adds |
|---|---|
| Entra ID sign-in logs | Real token validation, MFA status |
| PAM vault events | Detect privilege escalation patterns |
| VPN / ZTNA logs | Detect unusual network origin |
| Calendar / HR data | Flag access during leave or off-hours |

### 6.5 Compliance Coverage

| Standard | How TARE addresses it |
|---|---|
| NERC CIP | Continuous monitoring of critical asset access |
| NIS2 | Real-time incident detection and audit trail |
| ISO 27001 | Access control policy enforcement and logging |
| GDPR | Immutable audit log with downloadable evidence |

---

## 7. Summary — POC vs Production vs Future

```
                    POC (Now)             Production (Phase 2)    Future (Phase 3)
                    ─────────             ────────────────────    ───────────────
Agent Identity      Mock RBAC token       Entra ID JWT            Multi-IdP federation
Session Store       In-memory dict        Azure Redis             Distributed cache
Policy Engine       Hardcoded modes       OPA on Azure            Self-updating policies
Detection           4 rule-based signals  ML trained model        Continuous learning
Signal Sources      Agent commands only   Entra+PAM+VPN           Full SIEM integration
OT Layer            In-memory simulation  Real SCADA / OPC-UA     Digital twin
Response            FREEZE/DOWNGRADE/     Playbook automation     Autonomous remediation
                    TIMEBOX/SAFE
Audit Trail         Gateway log           Azure Sentinel          Regulatory dashboard
Case Management     Mock ServiceNow       Live ServiceNow API     Auto-escalation
Agents Covered      1 (GridOperator)      100s registered         All identity types
Human Loop          Approve / Deny UI     Full SOC workflow        AI-assisted triage
```

---

## 8. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, WebSockets |
| AI Agent | LangChain, Groq LLaMA (llama-3.1-8b-instant / llama-3.3-70b-versatile) |
| Detection Engine | Pure Python — tare_engine.py |
| ML Detection | scikit-learn — IsolationForest + RandomForest ensemble, joblib model persistence |
| ML Training Data | 6,200 synthetic sessions — NERC CIP baselines + MITRE ATT&CK ICS patterns |
| Frontend | React 18, Vite, pure CSS |
| Real-time | WebSocket push — no polling |
| LLM Explanation | Groq API with static fallback |
| Serving | Static React build served by FastAPI |

---

## 9. One Line Summary for Leadership

> TARE adds a continuous behavioural intelligence layer on top of existing
> identity infrastructure — catching compromised AI agents and identity theft
> in real time, before any harm reaches the grid, using the pattern of behaviour
> as the final and most powerful line of defence.

---

*TARE AEGIS-ID — Architecture & Roadmap Document*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: POC 2.0 — March 2026*
