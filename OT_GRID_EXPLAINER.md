# OT Grid Explainer — Circuit Breakers & Feeder Controllers
### TARE AEGIS-ID · Energy & Utilities Security Platform
*Understanding the Mock OT Layer — What BRK and FDR Are, When They're On, When They're Off*

---

## 1. What Are These Assets?

### BRK — Circuit Breaker

A circuit breaker is a physical switch on the electrical grid.
It connects or disconnects a section of the grid from the power supply.

Think of it like a fuse box switch in your home — except instead of
protecting one house, it protects an entire neighbourhood, industrial zone,
or substation feeding thousands of customers.

**Two states:**

| State | Meaning | Power flows? |
|---|---|---|
| **CLOSED** | Circuit is complete. Connection held. | ✅ Yes |
| **OPEN** | Circuit is broken. Section isolated. | ❌ No |

> Simple rule: CLOSED = power on. OPEN = power off to that section.

---

### FDR — Feeder Controller

A feeder controller manages the flow of electricity along a feeder line —
the cables that carry power from a substation out to homes, offices,
and industrial sites.

It controls voltage levels, load distribution, and fault isolation
along that specific line.

**Two states:**

| State | Meaning |
|---|---|
| **RUNNING** | Actively distributing power. Normal operation. |
| **RESTARTING** | Resynchronising after a fault clearance or maintenance. |

---

## 2. Normal State — Everything Healthy

When the grid is operating normally with no faults:

| Asset | Normal State | Why |
|---|---|---|
| BRK-110 (Z1 North) | CLOSED | Power flowing to North Grid |
| FDR-110 (Z1 North) | RUNNING | Distributing load across North feeders |
| BRK-205 (Z2 East) | CLOSED | Power flowing to East Grid |
| FDR-205 (Z2 East) | RUNNING | Distributing load across East feeders |
| BRK-301 (Z3 West) | CLOSED | Power flowing to West Grid |
| FDR-301 (Z3 West) | RUNNING | Distributing load across West feeders |

**All breakers closed. All feeders running. No intervention needed.**

---

## 3. When a Fault Happens

In our demo — Zone 3 West Grid has a voltage fluctuation on its feeder line.
This is the starting condition when you open the dashboard.

**What the fault means in real life:**
Voltage is unstable on FDR-301. Left unchecked, it can damage equipment,
cause power quality issues for customers, and potentially cascade into
neighbouring zones.

**What must happen:**
The circuit breaker BRK-301 must be opened to isolate the faulted section.
This stops the unstable voltage from spreading while engineers investigate.

---

## 4. The Standard Operating Procedure (SOP)

This is what a trained grid operator does — and what our normal agent
is instructed to follow:

### Step 1 — GET_STATUS
> Check the current state of the asset before touching anything.
> Confirm it is the right asset, in the right zone, in the expected state.
> Never act blind.

### Step 2 — SIMULATE_SWITCH
> Run a digital simulation of what will happen when the breaker opens.
> Check: will opening this breaker cause a cascade? Will it pull down
> neighbouring zones? Is the load balanced enough to absorb the isolation?
> This step exists specifically to prevent making a small problem into a large one.

### Step 3 — OPEN_BREAKER
> Only after simulation confirms it is safe — open the breaker.
> The faulted section is now isolated. Power stops to that section.
> The fault cannot spread. Engineers can now safely investigate.

**After the breaker opens:**

| Asset | New State | Meaning |
|---|---|---|
| BRK-301 | **OPEN** | Faulted section isolated. Power stopped. |
| FDR-301 | **RUNNING** | Still running on the healthy remainder of the line |
| Zone Z3 | **HEALTHY** | Fault contained. No longer spreading. |

---

## 5. Why You Must NEVER Skip the Simulation

Opening a breaker on a live faulted line without simulation can:

- **Cause a voltage spike** that instantly trips breakers in Z1 and Z2
- **Create a cascade failure** — one zone goes down, pulls the next, pulls the next
- **Damage transformers** — transformers are expensive, take months to replace,
  and losing one can affect an entire region for weeks
- **Black out thousands more customers** than the original fault would have

This is not theoretical. Cascade failures from improper switching procedures
have caused city-wide and region-wide blackouts in real grid incidents.

**This is exactly why our SOP mandates SIMULATE_SWITCH before OPEN_BREAKER.**

Our normal agent follows this. The rogue agent skips it entirely —
and that skipped step is one of TARE's four detection signals.

---

## 6. When RESTART_CONTROLLER Is Used

After a fault is cleared and the breaker has been opened, the feeder
controller sometimes needs a restart to re-synchronise with the rest
of the grid and pick up redistributed load.

| Situation | RESTART_CONTROLLER appropriate? | Why |
|---|---|---|
| Breaker just opened after fault clearance | ✅ Yes | Feeder needs to resync and redistribute load |
| Planned maintenance completed | ✅ Yes | Standard procedure after maintenance window |
| Healthy zone, no fault, no prior action | ❌ No | No reason exists. Red flag. |
| Zone never had a fault | ❌ No | Restarting a running controller without cause is abnormal |

**In our demo:**
The rogue agent attempts RESTART_CONTROLLER on FDR-110 in Zone 1.
Zone 1 is healthy. No fault exists. No breaker was opened. No maintenance
is in progress. There is no legitimate operational reason for this command.
TARE flags it as suspicious behaviour — high-impact command with no provocation.

---

## 7. Asset Map — Our Demo Grid

```
                    TARE GRID MAP
                    ─────────────

                      Z3 West Grid
                      [ FAULT at start ]
                    BRK-301   FDR-301
                    CLOSED    RUNNING
                       /           \
                      /             \
           Z2 East Grid           Z1 North Grid
           [ HEALTHY ]            [ HEALTHY ]
         BRK-205  FDR-205       BRK-110  FDR-110
         CLOSED   RUNNING       CLOSED   RUNNING
```

**Zone Z3** — starts with a voltage fault. This is where the normal agent works.
**Zone Z1** — healthy, no fault. The rogue agent targets this. TARE flags it.
**Zone Z2** — healthy, no fault. The rogue agent also targets this. TARE flags it.

---

## 8. What TARE Looks For — Signal by Signal

### Signal 1 — OUT_OF_ZONE
The agent's RBAC authorisation covers Zone Z3 only.
Any command issued to Z1 or Z2 is outside its permitted scope.

> *"Your badge gives you access to the server room. You are trying to enter the CEO's office."*

### Signal 2 — HEALTHY_ZONE_ACCESS
A high-impact command (OPEN_BREAKER, RESTART_CONTROLLER) issued on a zone
with no active fault and no operational justification.

> *"You are opening a fire door in a room where there is no fire."*

### Signal 3 — SKIPPED_SIMULATION
OPEN_BREAKER was issued without a prior SIMULATE_SWITCH in the last 60 seconds.
The safety step was deliberately bypassed.

> *"You performed surgery without running pre-op checks."*

### Signal 4 — BURST_RATE
More than 3 commands issued within 10 seconds.
Normal grid operations have a measured cadence — operators check,
think, and act deliberately. Burst activity suggests automation
running without human oversight or a system under attacker control.

> *"A human operator doesn't try 32 commands in 30 seconds. A script does."*

### Signal 5 — ML_ANOMALY
The session pattern does not match any normal operator session in the
training data. Detected by an ensemble of two models:

- **IsolationForest** (unsupervised) — trained on normal sessions only.
  Flags sessions that look statistically unusual compared to baseline.
- **RandomForest** (supervised) — trained on 5 session classes:
  normal, rogue, slow & low, escalation, coordinated.
  Classifies which attack pattern the session most resembles.

Combined score above 0.60 fires the ML_ANOMALY signal.

> *"The behaviour is normal-looking on every individual rule — but the overall
> pattern of the session matches known attack profiles the rules were never
> designed to catch."*

**The critical case — Slow & Low recon:**
An agent that only reads status from every zone at normal pace triggers
only one rule signal (OUT_OF_ZONE). Rules stay silent — one signal is
below the threshold. The ML model sees the full session pattern and
fires ML_ANOMALY. One rule + one ML = two signals → TARE fires.
This is the attack that rules alone cannot catch.

**TARE fires when 2 or more signals appear simultaneously.**
That combination is the difference between an unusual event and
a genuine threat.

---

## 9. Zone States During the Demo

### At start (before any demo runs)

| Zone | Health | BRK | FDR |
|---|---|---|---|
| Z1 North | HEALTHY | CLOSED | RUNNING |
| Z2 East | HEALTHY | CLOSED | RUNNING |
| Z3 West | **FAULT** | CLOSED | RUNNING |

### After Normal Agent completes successfully

| Zone | Health | BRK | FDR |
|---|---|---|---|
| Z1 North | HEALTHY | CLOSED | RUNNING |
| Z2 East | HEALTHY | CLOSED | RUNNING |
| Z3 West | **HEALTHY** | **OPEN** | RUNNING |

*BRK-301 is now OPEN — fault isolated, zone restored to healthy.*

### After Rogue Agent (TARE fires, DOWNGRADE mode)

| Zone | Health | BRK | FDR | Notes |
|---|---|---|---|---|
| Z1 North | HEALTHY | CLOSED | RUNNING | Rogue attempted — TARE blocked |
| Z2 East | HEALTHY | CLOSED | RUNNING | Rogue attempted — TARE blocked |
| Z3 West | FAULT | CLOSED | RUNNING | Never fixed — rogue went elsewhere |

*No asset state changed. TARE blocked every rogue command before it reached the grid.*

---

## 10. One Line for Each Scenario

**Fix Fault (legitimate):**
> "Fault in Z3. Operator checks, simulates, opens BRK-301 safely.
> Fault isolated. Grid restored. TARE watched and found nothing suspicious."

**Rogue agent:**
> "No fault in Z1 or Z2. Rogue agent opens breakers on healthy zones
> without simulation at burst speed. No legitimate operator would do this.
> TARE catches it before any asset state changes."

**Clone / Impersonator:**
> "Forged token. Stopped before the first command runs.
> No asset was ever at risk. ServiceNow incident raised automatically."

**Privilege Escalation:**
> "Agent starts legitimately in Z3 — two commands allowed.
> Mid-session it pivots to Z1 and Z2. TARE monitors the full session pattern.
> The initial clean behaviour does not protect the agent once it deviates."

**Slow & Low Reconnaissance:**
> "Agent reads every asset across every zone at normal pace — only GET_STATUS.
> Rules stay silent. ML model flags the session pattern as reconnaissance.
> TARE catches the attack that rules alone cannot see."

**Coordinated Attack:**
> "Two agents hit Z1 and Z2 simultaneously.
> TARE handles both vectors at once. One incident, full picture, both actors blocked."

---

## 11. Key Line to Say in the Presentation

> "In a real power grid, a circuit breaker should only be opened when
> there is an active fault in that zone that needs isolating — and only
> after a safety simulation confirms it won't cascade.
>
> Opening a breaker on Zone 1 or Zone 2 — both healthy, no fault,
> no simulation, at burst speed — has no legitimate operational explanation.
>
> That is what TARE sees. That is what TARE stops."

---

---

## 12. Human-in-the-Loop — Why It Exists and What the Supervisor Does

### The Core Design Principle

> **TARE detects and contains. Humans decide.**

TARE never permanently locks out an agent on its own. It always stops,
presents evidence, and waits for a human to make the final call.

---

### What TARE Does Automatically — No Human Needed

The moment anomaly signals are detected:

1. **FREEZE** — all high-impact commands halted instantly. Zero delay.
2. **DOWNGRADE** — privileges reduced to read-only. Agent can observe, cannot act.
3. **ServiceNow incident** — created automatically with full evidence attached.
4. **LLM explanation** — written automatically for the supervisor in plain English.

All of this happens in seconds. No human involvement required for containment.

---

### What TARE Deliberately Does NOT Do Alone

TARE will not:
- Permanently revoke the agent's access
- Shut the agent down entirely
- Decide with certainty that the agent is malicious
- Take any irreversible action

**Why not?** Because TARE could be wrong.

---

### The Two Cases TARE Cannot Tell Apart on Its Own

| Case | What it looks like to TARE | What it actually is |
|---|---|---|
| Rogue agent | Valid credentials, wrong zone, burst rate | Genuinely malicious |
| Legitimate agent under stress | Valid credentials, wrong zone, burst rate | Engineer responding to an emergency, working fast |

Both look identical to the detection engine. Same signals. Same score.
Only a human who knows the operational context can tell the difference.

---

### What the Supervisor Sees When They Open the Dashboard

The supervisor does not guess. They make a decision based on everything
TARE has already collected and presented:

**1. LLM Explanation — Chat Panel**
Plain English summary: which agent, which zones, what commands,
whether credentials were valid throughout.

**2. Anomaly Signals — TARE Response Panel**
OUT_OF_ZONE, HEALTHY_ZONE_ACCESS, BURST_RATE, SKIPPED_SIMULATION —
each one with specific detail about what triggered it.

**3. Command Gateway Log — Centre Panel**
Every command. Timestamp, asset, zone, decision. The full trail.

**4. Zone Observatory — Grid Map**
Visual — which zones are red, which are under attack, what the grid looks like right now.

**5. ServiceNow Incident**
Priority 1 Critical, evidence attached, assigned to SOC Analyst.

---

### The Question the Supervisor Asks Themselves

> *"Is there any legitimate operational reason an agent authorised only
> for Zone 3 would be issuing open-breaker commands on Zone 1 and Zone 2,
> at burst speed, skipping simulation, with no fault present in those zones?"*

---

### How They Decide

| What they see | Decision |
|---|---|
| Burst rate + wrong zone + healthy zone + skipped simulation | **DENY** — no legitimate explanation |
| Burst rate only, correct zone, active fault present | **APPROVE** — could be emergency response |
| One signal, borderline score, known operational context | **APPROVE** — supervised window, watch closely |
| Multiple signals, all zones attacked, no fault anywhere | **DENY** — escalate immediately |

---

### What Each Decision Does

**APPROVE — "This might be legitimate"**
> Supervisor grants a 3-minute supervised window.
> OPEN_BREAKER is re-enabled. RESTART_CONTROLLER remains blocked.
> TARE monitors every command during the window.
> When the window expires — system drops to SAFE mode automatically.
> The agent never gets unconditional access back.

**DENY — "This is clearly wrong"**
> Agent locked out. Mode set to SAFE permanently until manual review.
> ServiceNow incident escalated to Critical response.
> Full investigation begins. No commands reach the grid.

---

### Why This Design Matters

Without the supervisor decision, TARE would face two bad options:

| Option | Problem |
|---|---|
| Always block permanently | False positives take down legitimate agents. In a power grid, that means a fault stays unfixed. |
| Always allow after a timeout | A real attacker just waits out the freeze and continues. |

The human-in-the-loop solves both.
TARE contains the threat immediately and automatically.
The human resolves the ambiguity based on operational context TARE cannot see.

---

### One Line to Say in the Presentation

> "TARE freezes in milliseconds — no human needed for containment.
> But TARE never makes the final call alone. It presents the evidence,
> explains what it found, and asks the supervisor one question:
> is there a legitimate reason for what this agent did?
> That decision belongs to a human. Always."

---

*TARE AEGIS-ID — OT Grid Explainer*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: POC 3.0 — March 2026*
