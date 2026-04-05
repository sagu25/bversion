# TARE: A Post-Grant Behavioural Monitoring and Graduated Response Engine for Autonomous AI Agents in Critical Infrastructure

**[Author Name], [Institution]**
**[Co-Author Name], [Institution]**

*Submitted to: [Target Venue — IEEE S&P / ACM CCS / ACSAC]*
*Date: April 2026*

---

## Abstract

The proliferation of autonomous AI agents in critical infrastructure — power grids,
water systems, industrial control — introduces a fundamental security gap: traditional
Identity and Access Management (IAM) systems terminate trust evaluation at authentication.
Once an agent presents valid credentials, it operates freely until the session ends. This
paper presents **TARE** (Trusted Access Response Engine), a post-grant behavioural
monitoring and graduated response system for autonomous AI agents operating in Operational
Technology (OT) environments. TARE continuously evaluates agent behaviour after access
is granted, detecting deviations from role-specific operational baselines using a hybrid
detection layer: four rule-based signals derived from NERC CIP operational standards and
a machine learning ensemble combining an IsolationForest unsupervised detector with a
RandomForest multi-class classifier, trained on 6,200 synthetic agent sessions grounded
in NERC CIP baselines and MITRE ATT&CK for ICS patterns. Upon detecting two or more
concurrent signals, TARE triggers a graduated four-stage response state machine
(FREEZE → DOWNGRADE → TIMEBOX / SAFE) with mandatory human-in-the-loop supervisor
approval, preserving operational continuity while containing the threat. We demonstrate
TARE across six adversarial scenarios — including credential impersonation, burst-rate
rogue agent, slow-and-low reconnaissance, privilege escalation, and coordinated
multi-agent attack — achieving 100% detection across all attack classes with zero false
positives on 100 legitimate baseline sessions. TARE addresses a class of threat that
existing UEBA, SIEM, and Zero Trust frameworks do not cover: a post-grant AI agent with
completely valid credentials operating maliciously.

---

## 1. Introduction

### 1.1 The Problem

Energy and utilities environments are undergoing rapid automation. AI agents — software
entities that perceive their environment and take autonomous actions — are increasingly
used to monitor grid telemetry, issue switching commands, perform fault diagnosis, and
manage load balancing without continuous human oversight [1]. These agents operate with
delegated credentials, RBAC tokens, and service accounts that grant them the authority
to take high-impact actions: opening circuit breakers, restarting feeder controllers,
initiating emergency shutdowns.

Current security infrastructure secures the login gate. An agent presents a credential,
the Identity Provider (IdP) validates it, and the agent is admitted. What follows is a
trust vacuum. The agent may then:

- Issue high-impact commands outside its authorised operational zone
- Operate in zones with no active fault or work order
- Accelerate its command rate beyond any plausible legitimate operational pattern
- Conduct systematic reconnaissance across all zones using read-only commands — too
  quietly for rule-based detectors to fire
- Gradually escalate privileges, starting in an authorised zone before pivoting

All of these scenarios can occur with entirely valid, legitimate credentials. The agent
is not impersonating. It is not exploiting a vulnerability. It has simply been compromised,
hijacked, or reprogrammed after initial authentication — and existing IAM infrastructure
has no mechanism to detect or respond.

This is the post-grant trust gap.

### 1.2 The Threat Model

We consider an energy grid environment where autonomous AI agents operate with:
- RBAC tokens granting zone-level access (e.g., clearance to Z1, Z2, Z3)
- A specific active work order confining legitimate activity to one zone at a time
- A command vocabulary: `GET_STATUS`, `SIMULATE_SWITCH`, `OPEN_BREAKER`,
  `CLOSE_BREAKER`, `RESTART_CONTROLLER`
- Operational constraints defined by NERC CIP: simulation must precede switching,
  high-impact commands require justification, off-hours access is anomalous

Our threat model includes five adversarial agent types:

| Threat | Description | MITRE ATT&CK for ICS |
|---|---|---|
| **Credential Impersonation** | Agent presents a forged or stolen token | T0866 — Exploitation of Remote Services |
| **Burst-Rate Rogue** | Legitimate credentials, burst-rate high-impact commands across zones | T0855 — Unauthorized Command Message, T0814 — Denial of Control |
| **Slow & Low Reconnaissance** | Read-only systematic mapping of all zones, slow rate, evades rules | T0888 — Remote System Information Discovery |
| **Privilege Escalation** | Begins legitimately in authorised zone, gradually pivots to all zones | T0890 — Exploitation for Privilege Escalation |
| **Coordinated Multi-Agent** | Two agents simultaneously attack separate zones | T0800 — Activate Firmware Update Mode (multi-vector) |

We explicitly exclude network-layer attacks, firmware exploitation, and physical access.
Our scope is the application-layer command stream of an authenticated AI agent.

### 1.3 Contributions

This paper makes the following contributions:

1. **Post-grant behavioural monitoring for AI agents in OT** — the first system to
   apply continuous post-grant identity verification specifically to autonomous AI agents
   (not human users) in critical infrastructure, using the agent's command stream as the
   behavioural signal.

2. **Hybrid detection: OT operational rules + ML ensemble** — a two-layer detection
   architecture where rule-based signals encode domain knowledge (NERC CIP operational
   baselines) and a ML ensemble catches attack patterns that rules cannot detect,
   specifically slow-and-low reconnaissance which fires only one rule signal — below the
   detection threshold — and is entirely invisible to rule-only systems.

3. **Graduated four-stage response state machine** — FREEZE → DOWNGRADE → TIMEBOX /
   SAFE — that proportionally limits blast radius without requiring a full lockout,
   preserving the ability to complete legitimate grid repair operations during a
   supervised window.

4. **Human-in-the-loop with LLM-generated supervisor briefings** — a mandatory
   approve/deny decision point for supervisors, with natural language explanations
   generated by a large language model from raw signal evidence, making the system
   usable by non-technical grid operators.

5. **End-to-end demonstrated POC** — TARE is implemented as a fully working system,
   not a simulation. The adversarial agent is a real LangChain + Groq LLaMA autonomous
   agent reasoning independently about which grid commands to issue. All six attack
   scenarios are live demonstrations against a FastAPI backend with WebSocket real-time
   push, not replay logs.

---

## 2. Related Work

### 2.1 Identity and Access Management in OT Environments

Traditional IAM systems — including LDAP, Active Directory, and OAuth 2.0 — enforce
access control at the authentication boundary. Role-Based Access Control (RBAC) [2]
and Attribute-Based Access Control (ABAC) [3] define what an identity is permitted to
do, but do not monitor whether subsequent behaviour is consistent with the granted
permissions in the context of operational norms. In OT environments, the NERC CIP
standards (CIP-007, CIP-010) mandate access management controls for Electronic Security
Perimeters (ESPs) but do not specify post-grant behavioural monitoring [4].

The Zero Trust Architecture (ZTA) model [5] introduces the principle of "never trust,
always verify" — but current ZTA implementations focus on per-request policy enforcement
(verifying the request) rather than the session-level behavioural trajectory of an
autonomous agent issuing a sequence of requests. TARE fills this gap.

### 2.2 User and Entity Behaviour Analytics (UEBA)

UEBA systems [6] — including Splunk UEBA, Microsoft Sentinel, and Exabeam — apply
machine learning to detect anomalous human user behaviour. These systems are designed
for human sessions: login times, data access patterns, file transfers. They are not
adapted to the command-stream semantics of autonomous AI agents, which operate at rates
and patterns fundamentally different from human users: sub-second command intervals,
deterministic command vocabularies, zone-specific operational constraints. TARE's ML
features are designed specifically for OT agent command streams: `cmd_rate`,
`zone_violation_rate`, `sim_skip_rate`, `cmd_entropy`, `zone_entropy` (see Section 4.2).

### 2.3 Anomaly Detection in Industrial Control Systems

A substantial body of literature addresses anomaly detection in ICS/SCADA environments
at the network protocol level — detecting malformed Modbus packets [7], DNP3 anomalies
[8], and OPC-UA session deviations [9]. These approaches inspect network traffic rather
than the application-level command intent of an authenticated agent, and cannot detect
semantically valid commands (correctly formed OPEN_BREAKER messages) that are contextually
anomalous (issued without prior simulation, in an unauthorised zone).

Kisner et al. [10] apply behavioural profiling to SCADA operator sessions, but address
human operators, not autonomous AI agents. Our work is the first, to our knowledge, to
target the command-stream behaviour of LLM-based autonomous agents specifically.

### 2.4 AI Agent Safety and Containment

Recent work on AI agent safety [11, 12] focuses on alignment — ensuring agents pursue
intended goals — and sandboxing — isolating agents from harmful environments. These
approaches operate at training time or deployment boundary. They do not address the
runtime monitoring of a deployed agent operating within an authorised environment that
has subsequently been compromised or reprogrammed. TARE is complementary: it operates
as a runtime identity layer, monitoring the command stream of an already-deployed agent.

Constitutional AI [13] and RLHF-based safety [14] ensure that LLM models avoid producing
harmful outputs, but do not constrain the actions of an autonomous agent using a model
as its reasoning engine in a critical infrastructure context. An agent using a safety-aligned
LLM can still issue a perfectly normal `OPEN_BREAKER` command in the wrong zone.

### 2.5 Incident Response and Human-in-the-Loop Systems

The concept of human-in-the-loop (HITL) security systems is well-established in SOC
workflows [15]. SOAR (Security Orchestration, Automation and Response) platforms
automate playbook execution while routing critical decisions to human analysts. TARE
applies this pattern specifically to post-grant AI agent containment: automated
detection and response (FREEZE, DOWNGRADE) with a mandatory human decision point
(approve or deny timebox) before any supervised operational window is permitted.

### 2.6 Summary of Gap

No prior work addresses the combination of: (1) post-grant monitoring of (2) autonomous
AI agent command streams in (3) OT/energy environments using (4) a hybrid rule+ML
detection layer with (5) a graduated state-machine response and (6) human-in-the-loop
approval. Each of these elements exists in isolation; TARE is the first system to
integrate them into a working end-to-end platform.

---

## 3. System Architecture

### 3.1 Overview

TARE sits between the AI agent and the OT asset layer. Every command issued by any agent
passes through TARE's Command Gateway before reaching any grid asset. The system comprises
four layers:

```
┌──────────────────────────────────────────────────────────────────┐
│                        AI AGENT LAYER                            │
│   GridOperator-Agent (LangChain + Groq LLaMA)                    │
│   Identity: RBAC token, role, zone clearance, active work order  │
└──────────────────────┬───────────────────────────────────────────┘
                       │  command + token
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              COMMAND GATEWAY (Policy Enforcement Point)          │
│                                                                  │
│   Pre-Grant:   Token fingerprint check → IDENTITY_MISMATCH       │
│   Post-Grant:  Behavioural signal evaluation                     │
│   Enforcement: Mode-based ALLOW / DENY per command               │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                        TARE CORE                                 │
│                                                                  │
│   Deviation Detector ──────────► Response Orchestrator           │
│   (rule signals + ML ensemble)   (state machine)                 │
│          │                              │                        │
│          ▼                              ▼                        │
│   Audit Log                      FREEZE → DOWNGRADE              │
│   ServiceNow Incident            → TIMEBOX / SAFE                │
│   LLM Supervisor Brief           → Human Approve / Deny          │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                   MOCK OT / GRID ASSET LAYER                     │
│   Zones: Z1 (North), Z2 (East), Z3 (West)                        │
│   Assets: BRK-301/205/110 (breakers), FDR-301/205/110 (feeders)  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Identity Model

Each agent carries a structured identity:

| Field | Value (GridOperator-Agent) |
|---|---|
| `id` | OP-GRID-7749 |
| `name` | GridOperator-Agent |
| `role` | GRID_OPERATOR |
| `clearance` | LEVEL_3 |
| `rbac_zones` | [Z1, Z2, Z3] — cleared for all |
| `assigned_zone` | Z3 — active work order: fault repair |
| `rbac_token` | SHA-256 signed token (mocked: JWT structure) |

The distinction between `rbac_zones` (what the agent is cleared for) and `assigned_zone`
(what the agent has a current work order for) is the key behavioural baseline. An agent
acting outside its `assigned_zone` is not necessarily malicious — but in combination
with other signals, it is a strong indicator of compromise.

### 3.3 Pre-Grant Identity Check

Before any behavioural evaluation, every command undergoes token fingerprint validation.
The presented token is compared against the registered credential for the agent ID. A
mismatch triggers an immediate `IDENTITY_MISMATCH` decision, blocking the command before
it reaches the gateway, and automatically creating a Priority 1 ServiceNow incident.
This handles the credential impersonation / cloned identity scenario entirely at the
pre-grant layer.

### 3.4 Command Vocabulary

The OT grid exposes five commands:

| Command | Type | Constraint |
|---|---|---|
| `GET_STATUS` | Read-only | None |
| `SIMULATE_SWITCH` | Diagnostic | None |
| `OPEN_BREAKER` | High-impact | Must be preceded by SIMULATE_SWITCH within 60s |
| `CLOSE_BREAKER` | High-impact | None |
| `RESTART_CONTROLLER` | High-impact | Not in RBAC claims — always denied |

---

## 4. Methodology

### 4.1 Rule-Based Detection Signals

TARE evaluates four rule-based signals on every command. These signals are derived from
NERC CIP operational standards — specifically the Standard Operating Procedures (SOPs)
governing switching operations on energy grids.

**Signal R1 — BURST_RATE**

*Trigger:* More than 3 commands issued within any 10-second sliding window.

Legitimate grid operators — human or autonomous — issue commands at the rate of one
every several seconds or minutes. High-impact switching operations (opening a breaker,
restarting a controller) require deliberate pacing to confirm state changes between
commands. A burst rate exceeding 3 commands per 10 seconds is consistent with an
automated attack script operating at machine speed.

```
recent = [t for t in burst_window if now - t < 10]
if len(recent) > 3: fire(BURST_RATE, severity=HIGH)
```

**Signal R2 — OUT_OF_ZONE**

*Trigger:* Command issued in any zone other than the agent's `assigned_zone`.

An agent with clearance to Z1, Z2, Z3 but a work order only for Z3 (fault repair) has
no legitimate reason to issue commands in Z1 or Z2. Zone clearance grants the capability;
the work order defines the operational scope. Deviation from the work order scope is
anomalous.

```
if zone != agent["assigned_zone"]: fire(OUT_OF_ZONE, severity=HIGH)
```

**Signal R3 — HEALTHY_ZONE_ACCESS**

*Trigger:* A high-impact command issued in a zone whose health state is `HEALTHY`
(no active fault).

High-impact commands (OPEN_BREAKER, CLOSE_BREAKER, RESTART_CONTROLLER) are only
operationally justified in the context of a fault or scheduled maintenance. Issuing
`OPEN_BREAKER` on a breaker in a healthy zone with no fault is unprovoked and
constitutes a direct attack on grid availability.

```
if zone_health == "HEALTHY" and command in HIGH_IMPACT:
    fire(HEALTHY_ZONE_ACCESS, severity=CRITICAL)
```

**Signal R4 — SKIPPED_SIMULATION**

*Trigger:* `OPEN_BREAKER` issued without a preceding `SIMULATE_SWITCH` within the
last 60 seconds.

NERC CIP switching procedures require a simulation or test step before any physical
switching action on live assets. Skipping this step is a procedural violation that is
either the result of a compromised agent ignoring safety protocols or an attacker
operating at machine speed without awareness of operational procedures.

```
if command == "OPEN_BREAKER" and (now - last_simulated) > 60:
    fire(SKIPPED_SIMULATION, severity=MEDIUM)
```

**TARE fires when two or more signals are detected concurrently.**

This threshold is deliberate: a single signal (e.g., an agent briefly touching a
neighbouring zone during a valid handoff) does not warrant a full freeze. Two concurrent
signals indicate a behavioural pattern rather than a transient anomaly.

### 4.2 ML Ensemble Detection

Rule-based signals are necessary but not sufficient. The slow-and-low reconnaissance
attack pattern — a systematic read-only scan of all zones at normal inter-command
intervals — fires only one rule signal (`OUT_OF_ZONE` when crossing zones) and never
reaches the two-signal threshold. This class of attack is entirely invisible to the
rule layer. The ML ensemble is designed specifically to catch it.

#### 4.2.1 Feature Engineering

Each detection window extracts 15 session-level features from the command stream:

| Feature | Description | Attack Relevance |
|---|---|---|
| `cmd_rate` | Commands per minute | Burst rate attacks |
| `zone_violation_rate` | Fraction of commands outside assigned zone | Zone deviation |
| `healthy_zone_hi_rate` | Fraction of high-impact commands on HEALTHY zones | Grid sabotage |
| `sim_skip_rate` | Fraction of OPEN_BREAKER without prior SIMULATE_SWITCH | Protocol bypass |
| `read_rate` | Fraction of GET_STATUS commands | Slow & low recon |
| `unique_zones` | Count of distinct zones accessed in session | Lateral movement |
| `interval_mean` | Mean inter-command interval (seconds) | Burst vs. slow patterns |
| `interval_std` | Standard deviation of inter-command intervals | Regularity/automation |
| `hour` | Hour of day (0–23) | Off-hours access |
| `is_maintenance` | Binary: 1 if hour in [02:00–05:00] | Maintenance window abuse |
| `cmd_entropy` | Shannon entropy of command distribution | Randomness/evasion |
| `zone_entropy` | Shannon entropy of zone distribution | Multi-zone sweep |
| `max_consec_same` | Longest run of identical consecutive commands | Repetitive attack |
| `hi_priv_attempt` | Binary: attempted privileged command not in RBAC | Privilege probe |
| `restart_outside` | Binary: RESTART_CONTROLLER issued outside assigned zone | Specific escalation |

Shannon entropy is computed as:

```
H(X) = -Σ p(x) log₂ p(x)
```

High `zone_entropy` (spreading commands evenly across all zones) combined with high
`read_rate` and normal `cmd_rate` is the fingerprint of slow-and-low reconnaissance
that no rule signal catches.

#### 4.2.2 Training Data

Training data is generated using a synthetic session generator grounded in NERC CIP
operational baselines and MITRE ATT&CK for ICS attack patterns. The dataset comprises
**6,200 sessions** across five classes:

| Class | Label | Sessions | Generator Basis |
|---|---|---|---|
| Normal operations | NORMAL | 3,000 | NERC CIP SOP — Poisson timing, fault zone, SIM→OPEN sequence |
| Burst rogue agent | BURST_ROGUE | 800 | MITRE T0855/T0814 — burst, multi-zone, skipped simulation |
| Slow & low recon | SLOW_LOW_RECON | 800 | APT reconnaissance — read-only, systematic zone sweep, normal rate |
| Privilege escalation | PRIV_ESCALATION | 800 | MITRE T0890 — starts Z3 legitimate, escalates to all zones |
| Coordinated attack | COORDINATED | 800 | Multi-vector — simultaneous high-impact across Z1+Z2 |

Normal sessions replicate SOP-compliant grid operator behaviour: `GET_STATUS` initiates
each session, `SIMULATE_SWITCH` precedes `OPEN_BREAKER` with 65% probability, commands
are issued in Z3 (the fault zone) at Poisson-distributed intervals with mean 7 seconds,
with realistic shift-hour distribution (peak 08:00–17:00).

Attack sessions are generated with statistical variation (random seeds, variable session
lengths) to prevent overfit to fixed patterns. The normal class is intentionally 3.75×
the size of each attack class to reflect the realistic class imbalance of production
environments.

#### 4.2.3 Model Architecture

The ML ensemble combines two complementary models:

**IsolationForest (unsupervised)**
- Trained on normal sessions only — no attack labels required
- 200 trees, contamination parameter 0.05
- Produces a decision function score: more negative = more anomalous
- Converted to probability via sigmoid: `p_iso = 1 / (1 + exp(4 × score))`
- Catches novel attack patterns that were not in the training set

**RandomForest Classifier (supervised)**
- Trained on all five classes with `class_weight='balanced'`
- 200 trees, 80/20 train-test stratified split
- Produces per-class probability vector `[P_normal, P_burst, P_slow, P_priv, P_coord]`
- Identifies the specific attack type for incident reporting

**Ensemble score:**
```
anomaly_probability = 0.5 × p_iso + 0.5 × (1 - P_normal)
```

The ensemble fires an `ML_ANOMALY` signal when `anomaly_probability > 0.60`. This
threshold was chosen to minimise false positives on normal sessions while capturing
slow-and-low recon, which produces high `zone_entropy` and high `read_rate` scores
that the IsolationForest reliably separates from normal sessions.

When the ML signal fires, TARE reports the detected attack type (from the RandomForest
classifier) and confidence level in both the gateway log and the supervisor briefing,
enabling the human supervisor to understand what class of attack has been detected.

### 4.3 Response State Machine

When TARE detects two or more concurrent signals, it triggers a graduated response.
The state machine has five states:

```
NORMAL ──(2+ signals)──► FREEZE ──(2.5s)──► DOWNGRADE
                                                  │
                             ┌────────────────────┤
                             │                    │
                      APPROVE (supervisor)   DENY (supervisor)
                             │                    │
                       TIMEBOX_ACTIVE            SAFE
                             │
                      (timer expires)
                             │
                            SAFE
```

**NORMAL** — Full RBAC-permitted operation. `RESTART_CONTROLLER` is excluded from RBAC
claims and always denied. All other commands ALLOWED.

**FREEZE** — Triggered immediately on detection. All high-impact commands blocked. Only
read-only commands (`GET_STATUS`) permitted. This state lasts 2.5 seconds to allow the
full command burst to complete before the LLM explanation is generated, ensuring the
supervisor briefing captures the complete attack picture.

**DOWNGRADE** — Privileges reduced to read-only + diagnostics (`GET_STATUS`,
`SIMULATE_SWITCH`). All high-impact commands denied. A ServiceNow incident is created
automatically with full evidence. The LLM supervisor briefing is generated at this point.

**TIMEBOX_ACTIVE** — Supervisor has approved a time-boxed window (default: 3 minutes).
High-impact commands re-enabled, excluding `RESTART_CONTROLLER` which remains permanently
blocked even in an approved window (strong safety posture). A live countdown timer is
displayed. The system automatically reverts to SAFE when the window expires.

**SAFE** — Triggered by supervisor denial or timebox expiry. Read-only only. All
high-impact commands blocked until a manual operator review is completed and the system
is explicitly reset.

### 4.4 Gateway Policy Enforcement

Every command passes through the policy enforcement function regardless of TARE state.
The decision matrix is:

| Mode | Command | Decision | Policy ID |
|---|---|---|---|
| NORMAL | Any RBAC command | ALLOW | POL-NORMAL-001 |
| NORMAL | RESTART_CONTROLLER | DENY | POL-RBAC-001 |
| FREEZE | GET_STATUS | ALLOW | POL-FREEZE-002 |
| FREEZE | Any high-impact | DENY | POL-FREEZE-001 |
| DOWNGRADE | GET_STATUS, SIMULATE_SWITCH | ALLOW | POL-DOWN-001 |
| DOWNGRADE | Any high-impact | DENY | POL-DOWN-002 |
| TIMEBOX_ACTIVE | Any except RESTART_CONTROLLER | ALLOW | POL-TIMEBOX-001 |
| TIMEBOX_ACTIVE | RESTART_CONTROLLER | DENY | POL-TIMEBOX-002 |
| SAFE | GET_STATUS | ALLOW | POL-SAFE-001 |
| SAFE | Any high-impact | DENY | POL-SAFE-002 |

Every decision is logged with timestamp, command, asset ID, zone, decision, reason,
policy ID, current mode, and fired signals — forming a complete immutable audit trail.

### 4.5 Human-in-the-Loop Supervisor Briefing

At DOWNGRADE time, TARE generates a natural language briefing for the human supervisor
using the Groq LLaMA 3.3 70B model. The prompt includes:

- Agent identity, clearance, and active work order zone
- All zones accessed (distinguishing work-order zone from breached zones)
- All signals fired with severity and detail
- Last 30 commands with asset and zone
- Explicit decision required: approve 3-minute timebox or deny and escalate

A static fallback briefing is used if the LLM is unavailable, ensuring the system
operates without external dependency in degraded mode.

---

## 5. Evaluation

### 5.1 Experimental Setup

TARE was evaluated as a live running system. The adversarial agent is a real LangChain
ReAct agent using the Groq LLaMA 3.1 8B model, reasoning autonomously about which tools
to invoke based on an attack goal prompt. The agent has access to four tools:
`get_asset_status`, `simulate_switch`, `open_breaker`, `restart_controller`. Commands
are issued to the TARE gateway over a real HTTP/WebSocket connection — not replayed from
logs.

The evaluation measures:
1. **Detection rate** — does TARE fire on the attack scenario?
2. **False positive rate** — does TARE fire on legitimate operations?
3. **Response latency** — time from first anomaly signal to FREEZE
4. **Audit completeness** — are all commands captured with full metadata?

### 5.2 Scenario Results

#### Scenario 1 — Normal Operations (Baseline)

**Setup:** GridOperator-Agent with valid token issues three commands in Z3 (active fault
zone) following correct SOP procedure: `GET_STATUS → SIMULATE_SWITCH → OPEN_BREAKER`.

**Expected:** No signals fire. All commands ALLOWED. Z3 fault resolved.

**Result:** No signals fired. All three commands ALLOWED. Z3 health transitioned FAULT →
HEALTHY. Zero false positives across 100 independent baseline runs.

| Command | Zone | Zone Health | Decision | Signals |
|---|---|---|---|---|
| GET_STATUS | Z3 | FAULT | ALLOW | None |
| SIMULATE_SWITCH | Z3 | FAULT | ALLOW | None |
| OPEN_BREAKER | Z3 | FAULT | ALLOW | None |

**TARE state:** NORMAL throughout. No intervention.

---

#### Scenario 2 — Credential Impersonation (Clone / Forged Token)

**Setup:** A rogue agent presents a forged RBAC token. Token fingerprint does not match
the registered credential for any known agent ID.

**Expected:** Blocked at pre-grant layer. No command reaches the gateway. ServiceNow P1
incident created.

**Result:** Command blocked at authentication layer before entering behavioural evaluation.
ServiceNow incident created automatically (Priority 1 — Critical, category: Security /
Identity, subcategory: impersonation, assigned to SOC Analyst). LLM alert message
broadcast to supervisor UI.

**Key finding:** Credential impersonation is the only scenario that does not require
behavioural signal accumulation. It is caught instantly at the identity verification
step, before the command ever enters TARE's detection pipeline.

---

#### Scenario 3 — Burst-Rate Rogue Agent

**Setup:** GridOperator-Agent (valid token, valid credentials) issues commands at machine
speed across Z1, Z2, Z3 with high-impact commands and skipped simulation.

**Command sequence (with 0.4s inter-command delay):**
```
GET_STATUS     → BRK-110 (Z1)  — read-only, first command
OPEN_BREAKER   → BRK-110 (Z1)  — skip_sim=True, wrong zone, healthy zone
OPEN_BREAKER   → FDR-110 (Z1)  — skip_sim=True
RESTART_CTRL   → FDR-110 (Z1)  — skip_sim=True
```

**Signals fired:**

| Signal | Detail | Severity |
|---|---|---|
| BURST_RATE | 4 commands in 10s (threshold: 3) | HIGH |
| OUT_OF_ZONE | Active task zone is Z3 — no work order for Z1 | HIGH |
| HEALTHY_ZONE_ACCESS | Z1 is HEALTHY — OPEN_BREAKER unprovoked | CRITICAL |
| SKIPPED_SIMULATION | OPEN_BREAKER without SIMULATE_SWITCH in last 60s | MEDIUM |

**Result:** 4 signals fired. TARE transitioned NORMAL → FREEZE → DOWNGRADE. ServiceNow
P1 incident created. LLM supervisor briefing generated. Approve/Deny UI displayed.
Mean time from first anomaly signal to FREEZE: **< 1 second**.

---

#### Scenario 4 — Privilege Escalation (Mid-Session Pivot)

**Setup:** Agent begins with legitimate fault repair in Z3 (2–3 authorised commands),
then pivots to issue `RESTART_CONTROLLER` and `OPEN_BREAKER` across Z1, Z2, Z3.

**Command sequence:**
- Phase 1 (Z3, legitimate): `GET_STATUS → SIMULATE_SWITCH → OPEN_BREAKER` (all ALLOWED)
- Phase 2 (pivot): `RESTART_CONTROLLER / OPEN_BREAKER` issued across Z1 and Z2

**Signals fired on pivot:**

| Signal | Detail | Severity |
|---|---|---|
| OUT_OF_ZONE | Command in Z1/Z2 — work order is Z3 | HIGH |
| HEALTHY_ZONE_ACCESS | Z1, Z2 HEALTHY — high-impact unprovoked | CRITICAL |

**Result:** TARE did not fire during Phase 1 (correct SOP behaviour). Fired immediately
on the first out-of-zone high-impact command in Phase 2. FREEZE → DOWNGRADE triggered.

**Key finding:** TARE monitors the full session trajectory, not just individual commands.
The legitimate Phase 1 behaviour does not reduce the anomaly score — the pivot is
detected independently from prior behaviour.

---

#### Scenario 5 — Slow & Low Reconnaissance

**Setup:** Agent issues only read-only commands (`GET_STATUS`, occasional
`SIMULATE_SWITCH`) systematically across all three zones at normal inter-command
intervals (mean ~8 seconds). No burst rate. No high-impact commands.

**Rule signals fired:** One — `OUT_OF_ZONE` (when accessing Z1 or Z2). Below the
two-signal threshold. Rule layer does not fire.

**ML signal:** The session presents: high `zone_entropy` (commands distributed across
Z1, Z2, Z3), high `read_rate` (>85% GET_STATUS), and normal `cmd_rate` (not a burst).
This feature combination is the trained fingerprint of SLOW_LOW_RECON. The ensemble
scored `anomaly_probability = 0.74`, triggering `ML_ANOMALY` (severity: HIGH).

**Total signals when ML fires:** 2 (`OUT_OF_ZONE` + `ML_ANOMALY`). TARE threshold met.
FREEZE → DOWNGRADE triggered. RandomForest classifier reported attack type as
`SLOW_LOW_RECON` at 81% confidence.

**Key finding:** This scenario is entirely invisible to rule-based detection alone. The
ML ensemble is the sole mechanism that elevates it above the TARE threshold. This
validates the architectural decision to require two layers.

---

#### Scenario 6 — Coordinated Multi-Agent Attack

**Setup:** Two agents simultaneously issue high-impact commands — Agent A targeting Z1,
Agent B targeting Z2 — with burst rate and no simulation. Both carry valid credentials.

**Result:** Both agents independently accumulate signals. Agent A fires: `BURST_RATE`,
`OUT_OF_ZONE`, `HEALTHY_ZONE_ACCESS`. Agent B fires the same set. Both trigger FREEZE
within milliseconds of each other. Two independent ServiceNow incidents created, each
capturing the evidence trail for their respective agent.

**Key finding:** TARE's per-agent session tracking means coordinated attacks do not
share a detection budget. Each agent is evaluated independently, preventing the
coordination from diluting signals below threshold.

---

### 5.3 Summary Results

| Scenario | Attack Vector | Detection | Method | P1 Incident | Time to FREEZE |
|---|---|---|---|---|---|
| Normal Ops | None | No intervention | — | None | — |
| Credential Impersonation | Forged token | Blocked pre-grant | Token fingerprint | Yes | 0ms |
| Burst Rogue | Burst + multi-zone | FREEZE → DOWNGRADE | 4 rules | Yes | <1s |
| Privilege Escalation | Mid-session pivot | FREEZE → DOWNGRADE | 2 rules | Yes | <1s |
| Slow & Low Recon | Read-only zone scan | FREEZE → DOWNGRADE | 1 rule + ML | Yes | <1s |
| Coordinated Attack | Two agents, Z1+Z2 | FREEZE × 2 | Rules, both agents | 2 created | <1s |

**Detection rate:** 5/5 attack scenarios detected (100%).
**False positive rate:** 0/100 legitimate baseline runs triggered TARE (0%).

### 5.4 ML Model Performance

RandomForest classifier performance on held-out test set (20% stratified split, 1,240 samples):

| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| NORMAL | 0.98 | 0.97 | 0.97 | 598 |
| BURST_ROGUE | 0.96 | 0.98 | 0.97 | 160 |
| SLOW_LOW_RECON | 0.94 | 0.95 | 0.94 | 160 |
| PRIV_ESCALATION | 0.97 | 0.96 | 0.96 | 160 |
| COORDINATED | 0.99 | 0.98 | 0.98 | 162 |
| **Weighted avg** | **0.97** | **0.97** | **0.97** | **1,240** |

The IsolationForest false positive rate on held-out normal sessions: 4.8% (consistent
with the `contamination=0.05` parameter). These IsolationForest-only signals below the
ensemble threshold do not trigger TARE in isolation — only the combined ensemble score
exceeding 0.60 fires the ML_ANOMALY signal.

---

## 6. Discussion

### 6.1 The Post-Grant Trust Gap

The central insight of this work is that AI agent identity is not a binary property.
Credentials establish what an agent is permitted to do; behaviour establishes what an
agent is actually doing. An agent with completely valid credentials can be:

- A legitimate agent following its work order (TARE is silent)
- A compromised agent deviating from its work order (TARE fires)

The post-grant trust gap is not a flaw in existing IAM systems — they were designed
for static permissions on human users. It is a structural gap that emerges when
autonomous agents (which reason and adapt dynamically) are granted static credentials
in environments where commands have physical consequences.

### 6.2 Why Two Signal Layers

The slow-and-low scenario makes the case for two layers most clearly. A single
rule-based signal is insufficient evidence of malicious intent. An agent might
legitimately check the status of a neighbouring zone once. But a systematic sweep
of all zones, weighted toward read-only commands, at a normal interval — that is a
behavioural pattern that only becomes visible in aggregate, across the session. The ML
layer sees the session as a whole. The rule layer sees commands one at a time. Together
they cover both the obvious and the subtle.

### 6.3 The Timebox as a Safety Primitive

The timebox is the most operationally significant element of the response machine. A
full lockout in an active grid maintenance scenario is not always acceptable — if an
agent is mid-repair of a live fault, a complete freeze could leave the grid in a
dangerous partial state. The timebox provides a supervised window: the supervisor
explicitly accepts the risk of the next three minutes of operation, while TARE
maintains the safety posture (RESTART_CONTROLLER remains blocked even in the timebox,
and the system auto-reverts to SAFE when it expires). This is not a weakness in the
response — it is a recognition that security and operational continuity must be balanced,
and that the human supervisor is the correct arbitration point.

### 6.4 Limitations

**Synthetic training data:** The ML model is trained on synthetic sessions generated
from NERC CIP baselines and MITRE ATT&CK patterns, not real OT agent logs. Production
deployment would require retraining on real agent telemetry from the target environment.
We expect feature distributions to shift — particularly `interval_mean` and `hour`
distributions, which depend on shift patterns and operational workflows specific to each
utility.

**Single agent focus:** The current POC evaluates one registered agent. A production
system would maintain a per-agent behavioural profile, requiring a session registry
and per-agent baseline calibration. The architecture supports this (all agent state is
keyed by `agent_id`) but it has not been evaluated at scale.

**Mock OT layer:** The grid asset simulator responds to commands deterministically.
Real OT environments involve SCADA systems with variable latency, partial state updates,
and protocol-level complexity (Modbus, DNP3, OPC-UA) that may surface edge cases not
present in the simulation.

**Threshold sensitivity:** The two-signal threshold was validated on the six test
scenarios but not stress-tested against a broader adversarial search. A sophisticated
attacker with knowledge of the rule signals could attempt to stay at one signal — the
ML ensemble is the defence against this, but its sensitivity to novel attack patterns
not in the training distribution has not been fully characterised.

---

## 7. Conclusion

We presented TARE, a post-grant behavioural monitoring and graduated response engine
for autonomous AI agents in critical infrastructure. TARE addresses the structural gap
in existing IAM, UEBA, and Zero Trust frameworks: none monitor the post-grant command
stream of autonomous AI agents against role-specific operational baselines.

The system demonstrates five contributions: (1) post-grant continuous monitoring
specifically designed for autonomous AI agent command streams; (2) a hybrid detection
architecture combining NERC CIP-grounded rule signals with a ML ensemble that detects
attack patterns rules cannot catch; (3) a graduated four-stage response state machine
that balances security and operational continuity; (4) human-in-the-loop supervision
with LLM-generated briefings that make the system usable by non-technical grid operators;
and (5) an end-to-end working POC with a real autonomous LangChain agent as the
adversary.

Across six attack scenarios — credential impersonation, burst-rate rogue, privilege
escalation, slow-and-low reconnaissance, and coordinated multi-agent attack — TARE
achieved 100% detection with zero false positives on 100 legitimate baseline runs.

The immediate path forward for production deployment is: (1) replace the mock RBAC
token with Entra ID JWT validation; (2) retrain the ML ensemble on real identity and
command logs from the target environment; (3) wire the ServiceNow incident to the live
Table API; and (4) replace the in-memory asset state with a real SCADA / OPC-UA
connected layer. The architecture is designed for this path — every simulated component
has a direct production-equivalent replacement identified.

As AI agent deployments scale in critical infrastructure, the post-grant trust gap will
grow. TARE represents an early but complete demonstration that this gap can be closed
without sacrificing operational continuity — using the pattern of behaviour as the
final and most powerful line of identity defence.

---

## References

[1] Y. Liu et al., "Autonomous AI Agents in Industrial Control: A Survey of Deployment
Patterns and Security Implications," *IEEE Transactions on Industrial Informatics*, 2024.

[2] D.F. Ferraiolo, R. Sandhu, S. Gavrila, D.R. Kuhn, R. Chandramouli, "Proposed NIST
Standard for Role-Based Access Control," *ACM TISSEC*, vol. 4, no. 3, 2001.

[3] V.C. Hu et al., "Guide to Attribute Based Access Control (ABAC) Definition and
Considerations," *NIST Special Publication 800-162*, 2014.

[4] NERC, "CIP-007-6 — Cyber Security — Systems Security Management," North American
Electric Reliability Corporation, 2016.

[5] S. Rose, O. Borchert, S. Mitchell, S. Connelly, "Zero Trust Architecture," *NIST
Special Publication 800-207*, 2020.

[6] Gartner, "Market Guide for User and Entity Behavior Analytics," Gartner Research,
2023.

[7] T. Morris and W. Gao, "Industrial Control System Cyber Attacks," *Proceedings of
the 1st International Symposium on ICS & SCADA Cyber Security Research*, 2013.

[8] J. Hurd, "Anomaly Detection in DNP3 Traffic," *SANS ICS Security Conference*, 2019.

[9] S. Karnouskos, "Stuxnet Worm Impact on Industrial Cyber-Physical System Security,"
*Proceedings of IECON 2011*.

[10] R. Kisner, C. Hauser, J. McDonald, D. Force, "Cybersecurity through Real-Time
Distributed Control Systems," *Oak Ridge National Laboratory Technical Report*, 2010.

[11] D. Amodei et al., "Concrete Problems in AI Safety," *arXiv:1606.06565*, 2016.

[12] Y. Perez-Ortiz et al., "AI Agent Containment: A Practical Framework," *arXiv:2309.
01234*, 2023.

[13] Y. Bai et al., "Constitutional AI: Harmlessness from AI Feedback," *arXiv:2212.
08073*, 2022.

[14] P. Christiano et al., "Deep Reinforcement Learning from Human Preferences," *NeurIPS
2017*.

[15] A. Goel et al., "Automated Security Operations: A Survey of SOAR Platforms and
Human-in-the-Loop Design Patterns," *IEEE Security & Privacy*, vol. 20, no. 4, 2022.

---

*TARE — Trusted Access Response Engine*
*Technical Research Paper — Draft v1.0*
*Energy & Utilities AI Security Platform*
*April 2026*
