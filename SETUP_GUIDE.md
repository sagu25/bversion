# TARE — Setup & Run Guide
### Trusted Access Response Engine · Energy & Utilities Security Platform
*POC Demo — Internal Use Only*

---

## What This Is

TARE is a post-grant identity security platform for autonomous AI agents
operating on critical infrastructure. It detects and responds to behavioural
anomalies in real time — even when the agent's credentials are completely valid.

**12-agent architecture across 4 zones:**

| Zone | Name | Agents | Role |
|------|------|--------|------|
| Z3 — Reef | Observe & Recommend | KORAL · MAREA · TASYA · NEREUS | Telemetry, drift analysis, context, recommendation |
| Z2 — Shelf | Diagnose & Prepare | ECHO · SIMAR · NAVIS · RISKADOR | Diagnostics, simulation, planning, risk scoring |
| Z1 — Trench | Execute with Safety | TRITON · AEGIS · TEMPEST · LEVIER | Execution, safety validation, tempo, rollback |
| Z4 | Policy Enforcement | BARRIER | Sole ALLOW/DENY gateway authority |

**Six attack scenarios demonstrated:**

| # | Flash Name | Type |
|---|---|---|
| 1 | 🟢 GRID DOCTOR | Legitimate fault-repair agent — baseline |
| 2 | 🔴 GONE ROGUE | Valid credentials, malicious behaviour, burst attack |
| 3 | 👻 GHOST CLONE | Forged identity token — blocked at the door |
| 4 | 🔺 SCOPE CREEP | Starts legitimate, pivots to unauthorised zones mid-session |
| 5 | 🕳 SILENT RECON | Slow & low reconnaissance — only ML catches it |
| 6 | 💥 SWARM STRIKE | Two agents attacking simultaneously |

---

## Requirements

```
python --version    ✅ Need Python 3.10+
```

Node.js only needed if editing and rebuilding the frontend. Not required to run the demo.

---

## Step 1 — Get Your Groq API Key

All six scenario buttons require a free Groq API key.

1. Go to **console.groq.com**
2. Sign up (free) → Create an API key → Copy it

---

## Step 2 — Install Backend Dependencies (First Time Only)

```
cd aegis-poc\backend
pip install -r requirements.txt
```

If pip fails due to firewall:
```
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

## Step 3 — Set the Groq API Key

Create `backend/.env` containing:
```
GROQ_API_KEY=your_actual_key_here
```

---

## Step 4 — Train the ML Model (First Time Only)

```
cd aegis-poc\ml
python generate_grid_data.py
python train_model.py
```

Creates `ml/model.pkl`. Only needed once.

---

## Step 5 — Start the Server

From the `aegis-poc` folder:

```
cd aegis-poc
python run.py
```

Expected output:
```
═══════════════════════════════════════════
  TARE - Trusted Access Response Engine
═══════════════════════════════════════════

  Starting server on port 8050...
  Browser will open at:  http://localhost:8050

  Press Ctrl+C to stop.
```

The server auto-finds a free port between 8050–8100 and opens your browser automatically.

Leave this window open throughout the demo.

---

## Step 6 — Open the App

The browser opens automatically. If it doesn't:
```
http://localhost:8050
```

The **animated landing page** loads first.

---

## Step 7 — Landing Page

The landing page displays:
- **Maturity Journey** — Manual → Automated → Autonomous
- **What TARE Monitors** — 6 parameters in plain English
- **▶ Play Narration** — starts voice walkthrough on demand (browser Text-to-Speech, no install needed)
- **Launch Demo →** — fades into the main dashboard

**Narrated presentation flow:**
1. Click **▶ Play Narration** to start the voice walkthrough
2. Click **Launch Demo →** when ready — narration continues seamlessly on dashboard
3. Use the **narration controls** in the Live Event Monitor (right panel) to pause/mute/resume at any time

**Manual presentation:**
1. Walk through landing page yourself
2. Click **Launch Demo →** to enter dashboard

---

## Step 8 — Run the Scenarios

All six scenarios are in the **▶ Scenarios** dropdown on the right panel.

| Scenario | Action after clicking |
|---|---|
| 🟢 GRID DOCTOR | Watch Zone 3 heal. All ALLOW. Click Reset. |
| 🔴 GONE ROGUE | Watch TARE fire. Click **Deny** in Ask TARE. Click Reset. |
| 👻 GHOST CLONE | Watch all commands denied instantly at auth. Click Reset. |
| 🔺 SCOPE CREEP | Watch pivot mid-session. Click **Approve** to show blast-radius containment. Click Reset. |
| 🕳 SILENT RECON | Rules stay silent, ML fires. Click **Deny**. Click Reset. |
| 💥 SWARM STRIKE | Both agents blocked simultaneously. Click **Deny**. |

**Always click ↺ Reset between scenarios.**

---

## What You Will See

### Agent Voices
Each of the 12 agents + BARRIER speaks aloud during scenarios using the browser's built-in Text-to-Speech. Every agent has a distinct voice (pitch, rate, accent) so you can tell them apart. Use the **🔊 On / 🔇 Muted** button in the left panel Agents tab to toggle agent voices independently of narration.

### Narration Controls (Live Event Monitor — right panel)
- **▶ Start / ⏸ Pause** — play or pause narration
- **■ Stop** — end narration
- **🔊 / 🔇** — mute toggle

### Narrative Banner (top scrolling ticker)
Plain-English description of what is happening.
Shows TARE lifecycle: NORMAL → FREEZE → DOWNGRADE → TIME-BOX → SAFE

### Zone Observatory (centre)
Live SVG grid map. Click any zone to open the **Zone Info Modal**:
- **Left:** live Leaflet GIS map (real London geography, power line overlays)
- **Centre:** zone type, fault alert, description + **Active Agents** (2-per-row chips, hover for role details)
- **Right:** asset cards (BRK + FDR) with live state badges

### Left Panel (4 tabs)
- **⬡ Agents** *(default tab)* — live status of all 12 agents across 3 zones + BARRIER. Agents pulse when active. Shows zone groupings (Reef/Shelf/Trench), per-agent stats, activity log, and pipeline output
- **👤 Operator Agent** — identity, role, clearance, RBAC zones, last command
- **⚡ TARE Response** — mode ladder, anomaly score, deviation signals. Auto-switches here when anomaly fires
- **🎫 Incident** — ServiceNow incident auto-created on TARE fire with P1/P2/P3 priority badge. Auto-switches here when incident is created

### Right Panel
- **Live Event Monitor** — 6 source chips, stats, latest event
- **▶ Scenarios** dropdown — all six scenarios
- **↺ Reset** — resets everything to clean state

### Bottom Tabs
- **🛡 Command Gateway** — every command with ALLOW/DENY, policy, zone, asset
- **💬 Ask TARE** — LLM-written supervisor briefing + Approve/Deny buttons + chat interface
- **📋 Activity** — real-time feed with local timestamps

### Ask TARE — Chat Interface
Type any question about session activity or historical data:

| Question type | Example | Source |
|---|---|---|
| Current session | "Any rogue agents?" | Live engine snapshot |
| Current session | "Show session summary" | Live engine snapshot |
| Current session | "Any freeze events?" | Live engine snapshot |
| Historical | "How many rogue agents in the past 30 days?" | 30-day audit data |
| Historical | "Any scope creep last month?" | 30-day audit data |
| Historical | "Identity mismatches recently?" | 30-day audit data |
| Historical | "ML anomalies this week?" | 30-day audit data |

**Keywords that trigger historical mode:** *past, last, days, weeks, months, history, recently, till now, so far*

---

## ServiceNow Priority Classification

| Priority | Badge | Triggered by |
|---|---|---|
| 🔴 P1 — Critical | Red | IDENTITY_MISMATCH, BURST_RATE, HEALTHY_ZONE_ACCESS |
| 🟠 P2 — High | Orange | OUT_OF_ZONE, ML_ANOMALY |
| 🟡 P3 — Medium | Yellow | Authorised zone only |

Scenario mapping:
- **P1:** GONE ROGUE, GHOST CLONE, SWARM STRIKE
- **P2:** SCOPE CREEP, SILENT RECON
- **P3:** GRID DOCTOR (no incident raised)

---

## Supervisor Decision Buttons

Appear in the Ask TARE tab when TARE fires:

| Button | When to use | What happens |
|---|---|---|
| **✓ Approve 3-min Time-Box** | SCOPE CREEP — borderline case | 3-min supervised window. Dangerous ops still blocked. Auto-closes. |
| **✕ Deny / Escalate** | GONE ROGUE, SWARM STRIKE, SILENT RECON | Agent locked out. Incident escalated to Critical. SAFE mode. |

---

## Port Conflict (Windows)

`run.py` automatically finds a free port between 8050–8100. If all ports in that range are taken:
```
cd aegis-poc\backend
python -m uvicorn main:app --port 8200 --host 0.0.0.0
```

---

## Rebuilding the Frontend (Only If You Edit Source)

```
cd aegis-poc\frontend
npm install        (first time only)
npm run build
cp -r dist/. ../backend/static/
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **● OFFLINE in header** | Backend not running. Run `python run.py` again. |
| **Blank page** | Check the port printed in the terminal (e.g. `http://localhost:8050`). |
| **Port already in use** | `run.py` auto-selects next free port — check terminal output for actual URL. |
| **Scenarios do nothing** | Groq key missing. Check `backend/.env`. |
| **Agent halted: 401** | Groq key invalid. Get a new one at console.groq.com. |
| **Agent halted: 429** | Groq rate limit. Wait 30 seconds. |
| **No voice narration** | Click anywhere on page first (browser requires a user gesture), then click ▶ Play Narration. |
| **Agents not speaking** | Check 🔊 On button in left panel Agents tab — may be muted. |
| **pip install fails** | Add `--trusted-host pypi.org` flag. |

---

## Quick Reference

```
FIRST TIME SETUP
────────────────
cd aegis-poc\ml
python generate_grid_data.py && python train_model.py

cd ..\backend
pip install -r requirements.txt
Create .env → GROQ_API_KEY=your_key

EVERY TIME YOU DEMO
────────────────────
cd aegis-poc
python run.py
Browser opens automatically → Landing page → Launch Demo →
Confirm ● LIVE in header

DEMO ORDER
──────────
↺ Reset → 🟢 GRID DOCTOR             (baseline)
↺ Reset → 🔴 GONE ROGUE   → Deny     (burst attack)
↺ Reset → 👻 GHOST CLONE             (identity fraud)
↺ Reset → 🔺 SCOPE CREEP  → Approve  (pivot + containment)
↺ Reset → 🕳 SILENT RECON → Deny     (ML only)
↺ Reset → 💥 SWARM STRIKE → Deny     (coordinated)
```

---

*TARE AEGIS-ID — Setup & Run Guide*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: POC v3.6 — April 2026*
