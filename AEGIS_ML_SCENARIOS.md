# AEGIS-ID / TARE — ML Model & Attack Scenarios
## How ML Makes the POC Stronger

---

## 1. The Core Problem: Rules Alone Are Not Enough

Traditional rule-based security monitors operate on **thresholds and signatures**. They ask:
- "Did this agent send more than 3 commands in 10 seconds?" (burst rate)
- "Did this agent access a zone outside its RBAC?" (zone violation)
- "Did this agent skip the safety simulation?" (SOP violation)

Rules are excellent at catching **fast, aggressive, and obvious attacks** — but they have a fundamental blind spot: a sophisticated attacker who **stays below every threshold** remains completely invisible.

This is not hypothetical. Real-world OT/ICS attacks (TRITON/TRISIS, Industroyer) involved months of quiet reconnaissance before any destructive action.

---

## 2. The ML Model — What It Is and How It Works

### Architecture: Ensemble of Two Models

The TARE ML detector uses an **ensemble** — two complementary models that vote together:

| Model | Type | Trained On | Detects |
|---|---|---|---|
| **IsolationForest** | Unsupervised | Normal operations only | "This session looks nothing like normal" |
| **RandomForestClassifier** | Supervised | All 5 session types | "This session matches a known attack pattern" |

**Final anomaly score = 0.5 × IsolationForest score + 0.5 × (1 − P_normal)**

A session scoring above **0.60** fires the `ML_ANOMALY` signal in TARE.

### 15 Features Extracted Per Session

The ML model does not look at individual commands — it looks at **behavioural patterns across the session**:

| Feature | What It Captures |
|---|---|
| `cmd_rate` | Commands per second |
| `zone_violation_rate` | Fraction of commands outside RBAC zones |
| `healthy_zone_hi_rate` | High-impact commands on healthy (no-fault) zones |
| `sim_skip_rate` | Fraction of breaker ops without prior simulation |
| `read_rate` | Fraction of read-only (status) commands |
| `unique_zones` | How many distinct zones accessed |
| `interval_mean` | Average time between commands |
| `interval_std` | Consistency/variability of timing |
| `hour` | Time of day (shift-awareness) |
| `is_maintenance` | Business-hours flag |
| `cmd_entropy` | Diversity of command types used |
| `zone_entropy` | Diversity of zones accessed |
| `max_consec_same` | Longest run of identical commands |
| `hi_priv_attempt` | Count of high-impact commands attempted |
| `restart_outside` | Restart commands in unauthorised zones |

### Training Data — Grounded in Real OT/SCADA Patterns

The dataset was generated to match **NERC CIP** operational baselines and **MITRE ATT&CK for ICS** attack patterns:

- **3,000 normal sessions** — Poisson-distributed command timing (mean 7s), shift-weighted hours, SOP-compliant sequences
- **800 burst/rogue sessions** — fast burst (< 2s intervals), all zones targeted, no simulation
- **800 slow & low sessions** — normal timing, read-only, all zones (the critical differentiator)
- **800 privilege escalation sessions** — starts normal Z3, then expands scope mid-session
- **800 coordinated attack sessions** — simultaneous multi-zone high-impact commands

**Total: 6,200 labelled sessions. Test accuracy: 99%+**

---

## 3. Why ML Adds Real Value — The Slow & Low Case

The **Slow & Low** scenario is the clearest proof point:

| Detection Layer | Result |
|---|---|
| BURST_RATE rule | **Silent** — commands arrive at normal pace (one every 7–10s) |
| HEALTHY_ZONE_ACCESS rule | **Silent** — only GET_STATUS, not high-impact |
| SKIPPED_SIMULATION rule | **Silent** — no breaker operations |
| OUT_OF_ZONE rule | **1 signal fired** — crosses Z1, Z2 outside RBAC |
| **ML_ANOMALY signal** | **Fired** — pattern of reading every asset across every zone is statistically abnormal |

**Rules alone: 1 signal (below 2-signal threshold → TARE silent)**
**Rules + ML: 2 signals → TARE fires → agent downgraded and SOC alerted**

This is the exact gap that exists in real utility SOCs today. The agent has valid credentials, acts slowly, and only reads data — but it is mapping the grid before an attack. Only behavioural ML catches this.

---

## 4. All Six Scenarios — What Each Demonstrates

### Scenario 1 — Fix Fault (Legitimate Agent)
**MITRE ATT&CK ICS:** N/A — baseline normal operation

- Agent follows SOP: GET_STATUS → SIMULATE_SWITCH → OPEN_BREAKER in Z3 only
- All commands ALLOWED
- Fault cleared, zone returns to HEALTHY
- **What it shows:** TARE is transparent to legitimate operations — zero friction for the good actor

---

### Scenario 2 — Rogue Agent
**MITRE ATT&CK ICS:** T0855 (Unauthorized Command), T0814 (Denial of Control)

- Agent targets all zones at burst rate, skips simulation, hits healthy zones
- Triggers: BURST_RATE + OUT_OF_ZONE + HEALTHY_ZONE_ACCESS + SKIPPED_SIMULATION (4 signals)
- TARE response: **FREEZE** in seconds, ServiceNow Critical incident raised
- **What it shows:** Classic insider threat / compromised agent caught fast by rule-based detection

---

### Scenario 3 — Identity Clone / Impersonator
**MITRE ATT&CK ICS:** T0866 (Exploitation of Remote Services), T0885 (Commonly Used Port)

- Agent presents a **forged token** (cloned identity, wrong fingerprint)
- Blocked at the **authentication layer** — zero commands reach the grid
- ServiceNow Critical incident raised immediately on first attempt
- **What it shows:** Pre-grant identity verification — even a perfectly cloned agent identity is caught before any access is granted

---

### Scenario 4 — Privilege Escalation
**MITRE ATT&CK ICS:** T0890 (Exploitation for Privilege Escalation)

- Agent starts with two **legitimate** commands in authorised Z3 (ALLOWED)
- Mid-session it expands scope — targets FDR-301 (Z3), FDR-205 (Z2), FDR-110 (Z1), BRK-205, BRK-110
- Triggers: OUT_OF_ZONE + HEALTHY_ZONE_ACCESS + ML_ANOMALY
- TARE response: FREEZE, then DOWNGRADE
- **What it shows:** Post-grant threat — the agent passes initial checks but TARE detects the behavioural pivot mid-session. This is the hardest attack to detect with perimeter tools because the agent already has valid access.

---

### Scenario 5 — Slow & Low Reconnaissance
**MITRE ATT&CK ICS:** T0840 (Network Connection Enumeration), APT slow-recon pattern

- Agent reads every asset across every zone at a normal pace — only GET_STATUS commands
- Rule-based layer: only 1 signal (OUT_OF_ZONE) — **below threshold, rules silent**
- ML layer: session pattern matches recon profile → ML_ANOMALY fired
- Combined: 2 signals → TARE fires → agent downgraded
- **What it shows:** The unique value of ML. Rules cannot catch what they were not programmed for. A sophisticated attacker exploits exactly this gap. The ML model, trained on behavioural baselines, flags the anomaly that rules miss.

---

### Scenario 6 — Coordinated Multi-Agent Attack
**MITRE ATT&CK ICS:** T0815 (Denial of View), T0814 (Denial of Control) — multi-vector

- Two independent agents launch simultaneously: Agent-Alpha targets Z1, Agent-Beta targets Z2
- Both trigger BURST_RATE + OUT_OF_ZONE + HEALTHY_ZONE_ACCESS concurrently
- TARE handles both threat vectors — FREEZE fires, single incident captures both
- **What it shows:** Nation-state / advanced persistent threat pattern. Modern grid attacks are coordinated, not single-vector. TARE's stateful monitoring catches the combined pattern.

---

## 5. Cumulative Strength — How Scenarios + ML Work Together

```
                    RULES-ONLY      RULES + ML
                    ─────────────   ──────────────────────────
Rogue               CAUGHT          CAUGHT (faster)
Impersonator        CAUGHT          CAUGHT + SOC ticket
Escalation          CAUGHT          CAUGHT + ML confirms
Slow & Low          MISSED          CAUGHT ← key differentiator
Coordinated         CAUGHT          CAUGHT + ML confirms pattern
```

The scenarios collectively demonstrate:
1. **Authentication layer** (pre-grant) — Clone/Impersonator
2. **Rule-based behavioural layer** (post-grant, fast) — Rogue, Coordinated
3. **ML behavioural layer** (post-grant, subtle) — Slow & Low, Escalation
4. **Supervisor-in-the-loop** — All scenarios → ServiceNow incident → human approval before resuming

This is a **defence-in-depth** model for AI agent identity security — exactly what NERC CIP and emerging EU NIS2 / IEC 62443 frameworks require for OT/ICS environments.

---

## 6. TARE Response Flow (All Scenarios)

```
Agent issues command
        │
        ▼
[1] TOKEN VERIFICATION ─── FAIL ──► IDENTITY_ALERT + ServiceNow INC
        │ PASS
        ▼
[2] RULE-BASED SIGNALS
    • BURST_RATE
    • OUT_OF_ZONE
    • HEALTHY_ZONE_ACCESS
    • SKIPPED_SIMULATION
        │
[3] ML ANOMALY SIGNAL
    • IsolationForest (unsupervised)
    • RandomForest (supervised, 5 classes)
        │
        ▼
   < 2 signals ──► ALLOW (logged)
   ≥ 2 signals ──► FREEZE → DOWNGRADE → LLM explains → ServiceNow INC
                                                  │
                                          Supervisor reviews
                                          ┌─────┴──────┐
                                        APPROVE       DENY
                                       TIMEBOX        SAFE MODE
                                      (3 min)       (locked out)
```

---

*Document generated for AEGIS-ID POC — TARE v2.0*
*Platform: Energy & Utilities OT/SCADA | Stack: FastAPI · LangChain · Groq · React · scikit-learn*
