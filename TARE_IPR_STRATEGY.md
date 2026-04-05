# TARE — Intellectual Property Rights (IPR) Strategy
### Trusted Access Response Engine · Energy & Utilities AI Security Platform
*Internal Use Only — Confidential*

---

## Overview

TARE (Trusted Access Response Engine) represents a novel approach to AI agent identity
security in operational technology environments. This document outlines the two-track
IPR strategy: a **Technical/Research Paper** and a **Patent (Non-Provisional)**.

Both tracks protect different things. The paper establishes **scientific priority and
credibility**. The patent establishes **commercial exclusivity**. Together they form a
complete IP moat around the invention.

---

## Track 1 — Technical / Research Paper

### 1.1 What Makes TARE Paper-Worthy

TARE is novel in the following combination:
- Post-grant behavioural monitoring of AI agents in OT/energy environments
- A hybrid rule-based + ML ensemble detection layer (not either/or)
- A state-machine response system (FREEZE → DOWNGRADE → TIMEBOX → SAFE) with
  human-in-the-loop approval — not binary block/allow
- LLM-generated plain-English briefings for non-technical supervisors
- Demonstrated in a live POC with real AI agents (LangChain + Groq) making
  autonomous decisions against a simulated grid

No published paper currently combines all five of these in a single working system.

---

### 1.2 Paper Structure

#### a) Novel Contribution / Original Contribution
What is new about TARE that does not exist in the literature:

> "We present TARE, a post-grant identity behavioural monitoring engine for autonomous
> AI agents in critical infrastructure. Unlike traditional IAM systems that terminate
> trust assessment at authentication, TARE continuously evaluates agent behaviour
> post-grant using a hybrid detection layer — combining rule-based signals derived from
> NERC CIP operational baselines with an ML ensemble (IsolationForest + RandomForest)
> trained on 6,200 synthetic agent sessions. Detection triggers a four-stage graduated
> response state machine with mandatory human-in-the-loop approval, preserving
> operational continuity while containing threats."

Key novelty claims:
- Post-grant continuous identity verification for AI agents (not users)
- Hybrid detection: operational rules + ML ensemble, signals combined not siloed
- Graduated state machine response with time-boxed supervised windows
- Applied to OT/energy grid — NERC CIP-grounded baselines
- End-to-end demonstrated POC with autonomous LLM agents

#### b) Problem Statement
> AI agents operating in energy and utilities environments are granted credentials and
> then trusted indefinitely. Once authenticated, a compromised, hijacked, or rogue agent
> can issue destructive commands — open breakers, restart controllers, cause outages —
> while appearing legitimate. Traditional IAM infrastructure has no mechanism to detect
> or respond to post-grant identity deviation. As AI agent deployments scale in critical
> infrastructure, this gap becomes a critical attack surface.

Five threat vectors TARE addresses:
1. Rogue agent with valid credentials operating outside its authorised scope
2. Cloned / impersonator agent presenting a forged token
3. Legitimate agent hijacked mid-session
4. Privilege escalation from an authorised zone to an unauthorised one
5. Slow & low reconnaissance invisible to rule-based detection

#### c) Methodology
- **System architecture:** Command Gateway (PEP) → TARE Core (detection + response) → Mock OT Grid
- **Detection layer:** 4 rule-based signals + 1 ML ensemble signal
  - `BURST_RATE` — >3 commands in 10 seconds
  - `OUT_OF_ZONE` — command issued outside active work order zone
  - `HEALTHY_ZONE_ACCESS` — high-impact command on a fault-free zone
  - `SKIPPED_SIMULATION` — OPEN_BREAKER without prior SIMULATE_SWITCH
  - `ML_ANOMALY` — session pattern matched by IsolationForest + RandomForest ensemble
- **Response state machine:** NORMAL → FREEZE → DOWNGRADE → TIMEBOX_ACTIVE / SAFE
- **Human-in-the-loop:** Supervisor approve/deny with LLM-generated plain-English briefing
- **ML training:** 6,200 synthetic sessions, 3 classes (benign, anomalous, attack), NERC CIP
  baselines + MITRE ATT&CK ICS patterns
- **Evaluation:** 6 attack scenarios demonstrated live with autonomous LangChain agent

#### d) Results / Evaluation

| Scenario | Threat Vector | TARE Response | Outcome |
|---|---|---|---|
| Fix Fault | Authorised normal ops | Silent — no intervention | Zero false positive |
| Rogue Agent | Valid creds, wrong zone + burst | FREEZE → DOWNGRADE → TIMEBOX | Threat contained |
| Clone / Impersonator | Forged token | Blocked at auth layer — ServiceNow P1 | Identity theft blocked pre-grant |
| Privilege Escalation | Starts Z3, pivots to Z1/Z2 | FREEZE → DOWNGRADE | Mid-session pivot detected |
| Slow & Low Recon | Quiet read-only scan | ML_ANOMALY fires → FREEZE | Rules-invisible threat caught |
| Coordinated Attack | Two agents, Z1 + Z2 | FREEZE → DOWNGRADE both | Multi-vector contained |

Key metrics to report:
- True positive rate across 6 attack scenarios: **6/6 detected**
- False positive rate on legitimate operations: **0/100 (baseline runs)**
- Mean time from first anomaly signal to FREEZE: **< 1 second**
- Audit trail completeness: **100% — every command logged with decision + policy ID**

#### e) Conclusion / Summary (Key Findings)

1. Post-grant behavioural monitoring is **necessary and sufficient** to catch threats
   that pass authentication — valid credentials are not a trust guarantee.
2. The hybrid rule + ML approach catches threats that neither layer catches alone:
   rules miss slow & low; ML alone lacks operational explainability.
3. The FREEZE → DOWNGRADE → TIMEBOX state machine is operationally practical —
   it does not require a full lockout, preserving legitimate grid repair work.
4. Human-in-the-loop with LLM-generated supervisor briefings is demonstrably
   implementable and understandable by non-technical operators.
5. The POC is production-path-compatible — every simulated component has a
   direct Phase 2 production replacement (Entra ID, OPA, Azure Sentinel,
   live ServiceNow API).

#### f) Literature Survey / Citation Links

Key areas to survey (prior art baseline for both paper and patent):

| Area | Key Terms to Search |
|---|---|
| AI agent security | "LLM agent safety", "autonomous agent containment", "AI agent identity" |
| Behavioural anomaly detection | "UEBA energy grid", "insider threat detection OT" |
| Zero Trust in OT | "Zero Trust operational technology", "NERC CIP Zero Trust" |
| IAM post-grant monitoring | "continuous authentication", "post-grant access control" |
| ML anomaly detection ICS | "IsolationForest ICS", "SCADA anomaly detection ML" |

Recommended databases: IEEE Xplore, ACM Digital Library, arXiv (cs.CR), Google Scholar

Target venues:
- IEEE S&P (Security & Privacy)
- ACM CCS (Computer and Communications Security)
- ACSAC (Annual Computer Security Applications Conference)
- Usenix Security
- Industry: SANS ICS/SCADA track, RSA Conference

---

## Track 2 — Patent (Non-Provisional, USPTO)

### 2.1 What is Patentable in TARE

A patent protects the **method** and **system** — not the idea in general, but the
specific mechanism. TARE's patentable core:

> A computer-implemented method for post-grant behavioural monitoring and graduated
> response enforcement for autonomous AI agents in operational technology environments,
> comprising: (1) a command gateway policy enforcement point that evaluates identity
> pre-grant and behavioural signals post-grant; (2) a hybrid detection engine combining
> rule-based operational deviation signals with a machine learning ensemble trained on
> role-specific behavioural baselines; (3) a graduated response state machine with
> time-boxed human-in-the-loop approval; and (4) automated case creation in a security
> incident management system upon threat detection.

### 2.2 Patent Filing Pathway

#### Step 1 — Invention Disclosure (IPD / IDF)
Before filing, document the invention internally:
- What was invented (the TARE system — detection + response)
- Who invented it (list all contributors)
- When it was first reduced to practice (POC completion date)
- What problem it solves that was not solved before
- How it differs from prior approaches

**File this before any public disclosure** (conference talk, paper submission, demo to
external parties). Public disclosure starts a 12-month clock in the US (grace period)
but kills rights in most other countries immediately.

#### Step 2 — Prior Art Search

**Tools:**
- [USPTO Patent Full-Text Database](https://patents.google.com) — Google Patents
- [Espacenet](https://worldwide.espacenet.com) — European Patent Office global database
- IEEE Xplore / ACM DL — academic prior art
- Google Scholar

**Search terms for TARE:**
```
"AI agent" AND "behavioural monitoring" AND "access control"
"post-grant" AND "identity" AND "anomaly detection"
"autonomous agent" AND "operational technology" AND "security"
"zero trust" AND "AI agent" AND "critical infrastructure"
"UEBA" AND "AI agent" AND "OT"
"command gateway" AND "policy enforcement" AND "machine learning"
"graduated response" AND "identity" AND "anomaly"
```

**Goal of prior art search:**
- Confirm novelty — find what is closest and document how TARE differs
- Inform claim drafting — write claims around the gap in prior art
- Strengthen the application — anticipate examiner rejections (obviousness, prior art)

#### Step 3 — Non-Provisional Patent Application

File directly as a **Non-Provisional Utility Patent** (USPTO):

**Application structure:**

| Section | Content |
|---|---|
| **Title** | System and Method for Post-Grant Behavioural Monitoring and Graduated Response Enforcement of Autonomous AI Agents in Operational Technology Environments |
| **Abstract** | 150 words max — high-level summary of the invention |
| **Specification** | Detailed description of the system — architecture, detection engine, state machine, human-in-the-loop |
| **Drawings** | System architecture diagram, state machine diagram, signal detection flow, UI screenshots |
| **Claims** | The legally protected scope — most important part |

**Claims strategy (draft):**

*Independent Claim 1 (broadest — method):*
> A computer-implemented method comprising: receiving, at a command gateway, a command
> from an autonomous AI agent along with an identity credential; verifying the credential
> against a registered identity store; upon successful pre-grant verification, evaluating
> the command against a plurality of behavioural deviation signals derived from a
> role-specific operational baseline; when two or more deviation signals are detected,
> transitioning a response state machine from a normal operating mode to a freeze mode
> in which high-impact commands are blocked; generating an automated incident record in
> a security case management system; presenting a human supervisor with an AI-generated
> explanation of detected signals; and transitioning to a time-boxed operating mode upon
> supervisor approval or a safe mode upon supervisor denial.

*Dependent claims (narrow, add value):*
- Claim 2: The method of Claim 1, wherein the behavioural deviation signals include
  burst rate, zone deviation, healthy zone access, skipped simulation, and ML ensemble
  anomaly score.
- Claim 3: The method of Claim 1, wherein the ML ensemble comprises an IsolationForest
  model and a RandomForest classifier trained on role-specific operational baselines.
- Claim 4: The method of Claim 1, wherein the time-boxed operating mode expires
  automatically after a supervisor-approved duration, reverting to safe mode.
- Claim 5: System claims (apparatus) — mirroring method claims

**Filing fees (USPTO, 2025 estimate):**
- Micro entity (individual / small startup): ~$320 filing + $800 search + $400 exam
- Small entity (company <500 employees): ~$640 + $1,600 + $800
- Consider Provisional Patent first ($330 micro) to establish priority date while
  completing the full application — gives 12 months to file non-provisional

---

## 2.3 Copyright Protection (Automatic)

Copyright on TARE source code is **automatic** — it attaches the moment the code is
written and does not require filing. However, registering with the US Copyright Office
($65 online) enables statutory damages in litigation.

What copyright protects:
- The source code of `tare_engine.py`, `main.py`, `aegis_engine.py`, `ml_detector.py`
- The frontend React application
- Documentation, architecture diagrams, demo scripts

What copyright does **not** protect:
- The idea or method (that is what the patent covers)
- The algorithm itself in abstract form

**Action:** Register copyright for the codebase as a software package once the POC is
finalised. Keep version-controlled copies with timestamps as evidence of creation dates.

---

## Summary — Two-Track IPR Plan

| Track | What It Protects | Timeline | Cost |
|---|---|---|---|
| Technical Paper | Scientific priority, credibility, citations | Submit within 3-6 months | Time only |
| Patent — Non-Provisional | Commercial exclusivity on the method + system | File before any public disclosure | $1,200–2,400 (micro/small entity) |
| Copyright | Source code, UI, documentation | Automatic — register for full protection | $65 |

**Recommended order of operations:**
1. Complete Invention Disclosure internally (this week)
2. File Provisional Patent — locks priority date, low cost, 12-month window
3. Conduct prior art search — informs both paper and full patent claims
4. Submit Technical Paper to target venue
5. File Non-Provisional Patent within 12 months of provisional
6. Register copyright on final codebase

---

*TARE — IPR Strategy Document*
*Energy & Utilities AI Security Platform — Internal Use Only*
*Version 1.0 — April 2026*
