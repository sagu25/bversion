# AEGIS-ID / TARE — Future Scope & Product Roadmap
### Trusted Access Response Engine · Energy & Utilities Security Platform
*Strategic Vision Document — Internal Use Only*

---

## Where We Are Today (POC — Proved)

The current proof of concept demonstrates a working **post-grant behavioural
security layer** for AI agents on OT/ICS infrastructure. Six attack scenarios
are live, ML detection is active, and the human-in-the-loop workflow is functional.

The POC proves one critical thing:
> *An AI agent with completely valid credentials can still be a security threat.
> TARE catches it — post-grant, in real time, through behaviour — before any
> harm reaches the grid.*

---

## The Bigger Vision — Three Phases

```
Phase 1 (POC — Done)        Phase 2 (Production)         Phase 3 (Platform)
────────────────────         ────────────────────         ──────────────────
Post-grant behavioural   →   Production-grade TARE    →   Full AI Agent
monitoring for AI agents     on real infrastructure        Security Platform
```

---

## Phase 2 — Production-Grade TARE

### 2.1 Real Identity Infrastructure

| POC (Today) | Phase 2 |
|---|---|
| Mock RBAC token | Microsoft Entra ID JWT tokens |
| Single hardcoded agent | Agent identity registry — 100s of agents |
| In-memory session state | Azure Redis distributed cache |
| Hardcoded policy logic | Open Policy Agent (OPA) — policy as code |
| Gateway log only | Azure Sentinel immutable audit log |
| Mock ServiceNow ticket | Live ServiceNow Table API integration |

### 2.2 Real OT/ICS Connectivity

| POC (Today) | Phase 2 |
|---|---|
| In-memory grid simulation | OPC-UA / Modbus protocol adapter |
| 3 zones, 6 assets | Real SCADA-connected assets |
| Simulated fault states | Live telemetry from grid hardware |
| Python asset dict | Digital twin with real-time synchronisation |

### 2.3 Enhanced ML Detection

The ML model exists in the POC. Phase 2 makes it production-grade:

- Ingest 30+ days of real identity logs from Entra ID and PAM systems
- Train on actual agent behaviour baselines per role and shift pattern
- Continuously retrain — feedback loop from confirmed incidents
- Explainability layer — tell the supervisor *why* the model flagged the session

### 2.4 Graduated Response Levels

The POC has 2 response levels (FREEZE → DOWNGRADE). Phase 2 adds granularity:

| Level | Anomaly Score | Action |
|---|---|---|
| 1 — Monitor | 20–35 | Log silently, notify agent owner by email |
| 2 — Warn | 36–50 | Visible warning to supervisor, no restriction yet |
| 3 — Restrict | 51–65 | Reduce permissions temporarily — read-only for 10 minutes |
| 4 — Freeze | 66–80 | Halt high-impact ops, supervisor approval required |
| 5 — Block | 81–100 | Full lockout, SOC alert, automated playbook trigger |

### 2.5 Additional Signal Sources

| Signal Source | What It Adds |
|---|---|
| Entra ID sign-in logs | Real token validation, MFA status, sign-in anomalies |
| PAM vault events | Privilege escalation detection across systems |
| VPN / ZTNA logs | Flag access from unusual network locations |
| Calendar / HR data | Off-hours access, access during leave periods |
| Peer group comparison | "This agent is behaving differently from similar agents" |

---

## Phase 3 — AI Agent Security Platform

This is the full vision. TARE becomes a platform covering the **entire lifecycle
of AI agent identity security** — from provisioning to decommission.

---

### 3.1 CIEM for AI Agents — Entitlement Management

**The gap:** Existing CIEM tools (Saviynt, Ermetic, CyberArk) were built for
human users and cloud resources. They cannot understand agentic workloads —
what an AI agent actually needs access to, versus what it has been granted.

**What TARE adds:**

| Feature | What It Does |
|---|---|
| **Entitlement vs Usage Gap** | "Agent is authorised for Z1, Z2, Z3 — but in 90 days has only ever used Z3. Recommend restricting to Z3 only." |
| **Privilege Creep Detection** | "This agent's RBAC scope has expanded from 1 zone to 3 zones over 6 months — no business justification on record." |
| **Least Privilege Recommendation** | Based on 90 days of behavioural data, auto-suggest the minimum permission set needed for each agent role. |
| **Dormant Entitlement Alerts** | "Agent OP-GRID-7749 has EMERGENCY_SHUTDOWN permission — not used once in 12 months. Remove it." |
| **Entitlement Risk Scoring** | Score each agent's permission set against actual usage — flag over-privileged agents before they are exploited. |

**Why this is different from existing CIEM:**
Existing tools look at what permissions *exist*. TARE also looks at what an
agent actually *does* — combining entitlement data with behavioural data for
a complete picture. No current CIEM tool does this for AI agent workloads.

---

### 3.2 Agent Identity Lifecycle Management

| Stage | Capability |
|---|---|
| **Onboarding** | Automated identity provisioning for new AI agents — assign role, RBAC zones, permitted commands based on job function |
| **Baseline Learning** | 30-day behavioural learning period — build the normal profile before enforcement starts |
| **Active Monitoring** | Continuous post-grant monitoring (current TARE POC) |
| **Periodic Review** | Quarterly access certification — "does this agent still need these permissions?" |
| **Offboarding** | Automated deprovisioning when an agent is retired — revoke all entitlements, close open sessions |

---

### 3.3 Multi-Agent Coordination Intelligence

As organisations run hundreds of AI agents simultaneously, new threats emerge
that single-agent monitoring cannot catch:

| Threat | What It Looks Like | TARE Response |
|---|---|---|
| **Agent collusion** | Two agents with different access levels coordinate — one reads, the other acts | Cross-agent session correlation |
| **Relay attack** | Agent A passes a command to Agent B to execute (A can't, B can) | Command chain tracking |
| **Distributed recon** | 10 agents each read one zone — no single agent looks suspicious | Population-level anomaly detection |
| **Coordinated timing** | Multiple agents act simultaneously to overwhelm defences | Already demonstrated in POC (Coordinated scenario) |

---

### 3.4 Autonomous Remediation

Phase 3 moves beyond human-in-the-loop for lower-severity incidents:

| Severity | Human Role | TARE Action |
|---|---|---|
| Low (score < 40) | None needed | Auto-restrict, auto-log, auto-notify |
| Medium (score 40–65) | Notified, not required | Auto-restrict + auto-draft incident report |
| High (score 65–80) | Must approve/deny | FREEZE + await supervisor decision (current POC) |
| Critical (score > 80) | SOC Analyst assigned | Full lockout + playbook trigger + auto-escalation |

---

### 3.5 Regulatory & Compliance Dashboard

| Standard | TARE Coverage |
|---|---|
| **NERC CIP** | Continuous monitoring of critical cyber assets, access control enforcement, audit trail |
| **NIS2 (EU)** | Real-time incident detection, 72-hour reporting capability, evidence package |
| **IEC 62443** | Zone and conduit security for OT networks, identity-based access control |
| **ISO 27001** | Access control policy enforcement, incident management, logging |
| **NIST CSF 2.0** | Govern → Identify → Detect → Respond → Recover lifecycle coverage |

Automated compliance evidence export — regulators get a structured evidence
package, not a manual audit spreadsheet.

---

### 3.6 Integration Ecosystem

| System | Integration |
|---|---|
| Microsoft Sentinel | Bi-directional — TARE feeds incidents, Sentinel feeds signal enrichment |
| Splunk | TARE event stream → Splunk index for SOC correlation |
| ServiceNow | Live incident creation, automatic state updates, evidence attachment |
| PagerDuty / OpsGenie | Critical alert routing to on-call engineer |
| Microsoft Entra ID | Real JWT validation, Conditional Access policy enforcement |
| CrowdStrike | Cross-correlate agent identity events with endpoint telemetry |
| Palo Alto XSOAR | TARE incident triggers automated SOC playbook |

---

## Market Positioning

```
                        PRE-GRANT              POST-GRANT
                        (Who gets in?)         (What do they do after?)

Human Identities        Okta, Entra ID         UEBA (Splunk, Securonix)
                        CyberArk PAM

AI Agent Identities     Basic token check      ← TARE fills this gap →
                        (no existing           (no existing tool)
                         dedicated tool)
```

**The white space TARE occupies:**
No enterprise security vendor today provides post-grant behavioural monitoring
specifically designed for AI agents on operational technology infrastructure.
CIEM tools, PAM tools, and UEBA tools were all built for human users.
Agentic AI is a new and growing attack surface — and it is currently unmonitored.

---

## Why Now

| Trend | Implication for TARE |
|---|---|
| AI agents in enterprise growing 10x by 2027 (Gartner) | Massive new attack surface, no security tooling exists |
| EU NIS2 Directive enforcement active 2024 | OT operators legally required to monitor AI-driven access |
| NERC CIP evolving to cover AI-initiated commands | Utilities need an audit trail for agent actions |
| Nation-state attacks on grid infrastructure rising | Coordinated, slow & low attacks becoming standard TTPs |
| No vendor has shipped an AI agent security product | First-mover advantage in a category we helped define |

---

## One Line for Each Audience

**For the grant committee:**
> *"TARE is the missing security layer between AI agent authentication and the
> grid — we prove the concept today, and the roadmap scales it to a platform
> that no existing vendor offers."*

**For a utility CISO:**
> *"Every AI agent you deploy today has valid credentials and zero behavioural
> oversight after it authenticates. TARE fixes that."*

**For a technical evaluator:**
> *"Post-grant identity security with ML anomaly detection, human-in-the-loop
> approval, and a clear path to CIEM-grade entitlement management — all
> purpose-built for agentic workloads on OT infrastructure."*

---

*AEGIS-ID / TARE — Future Scope & Product Roadmap*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: 1.0 — March 2026*
