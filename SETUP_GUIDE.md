# TARE — Setup & Run Guide
### Trusted Access Response Engine · Energy & Utilities Security Platform
*POC Demo — Internal Use Only*

---

## What This Is

TARE is a post-grant identity security platform for autonomous AI agents
operating on critical infrastructure. It detects and responds to behavioural
anomalies in real time — even when the agent's credentials are completely valid.

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
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\backend
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
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\ml
python generate_grid_data.py
python train_model.py
```

Creates `ml/model.pkl`. Only needed once.

---

## Step 5 — Start the Server

```
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\backend
python -m uvicorn main:app --port 8002 --host 0.0.0.0
```

Expected output:
```
INFO: Uvicorn running on http://0.0.0.0:8002
INFO: Application startup complete.
```

Leave this window open throughout the demo.

---

## Step 6 — Open the App

```
http://localhost:8002
```

The **animated landing page** loads first.

---

## Step 7 — Landing Page

The landing page displays:
- **Maturity Journey** — Manual → Automated → Autonomous (enlarged cards, projection-ready)
- **What TARE Monitors** — 6 parameters in plain English
- **▶ Play Narration** — starts automated voice walkthrough (browser Text-to-Speech, no install needed)
- **Launch Demo →** — fades into the main dashboard

**Narrated presentation flow:**
1. Click **▶ Play Narration** — voice starts automatically
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

### Left Panel
- **Operator Agent** — identity, role, clearance, RBAC zones, last command
- **TARE Response Engine** — mode ladder, anomaly score, deviation signals
- **ServiceNow Incident** — auto-created on TARE fire with P1/P2/P3 priority badge

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

If you see `ERROR: [Errno 10048]`:
```
python -m uvicorn main:app --port 8003 --host 0.0.0.0
```
Increment (8002 → 8003 → 8004) until it starts. WebSocket URL updates automatically.

---

## Rebuilding the Frontend (Only If You Edit Source)

```
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\frontend
npm install        (first time only)
npm run build
cp -r dist/. ../backend/static/
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **● OFFLINE in header** | Backend not running. Start uvicorn again. |
| **Blank page** | Must be `http://localhost:8002` not port 5173. |
| **Port already in use** | Increment port number. |
| **Scenarios do nothing** | Groq key missing. Check `backend/.env`. |
| **Agent halted: 401** | Groq key invalid. Get a new one at console.groq.com. |
| **Agent halted: 429** | Groq rate limit. Wait 30 seconds. |
| **No voice narration** | Browser needs a user gesture first — click anywhere on page, then Play Narration. |
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
cd aegis-poc\backend
python -m uvicorn main:app --port 8002 --host 0.0.0.0
Open: http://localhost:8002
Landing page → Play Narration (optional) → Launch Demo →
Confirm ● LIVE in header

DEMO ORDER
──────────
↺ Reset → 🟢 GRID DOCTOR             (baseline)
↺ Reset → 🔴 GONE ROGUE   → Deny     (burst attack)
↺ Reset → 👻 GHOST CLONE             (identity fraud)
↺ Reset → 🔺 SCOPE CREEP  → Approve  (pivot + containment)
↺ Reset → 🕳 SILENT RECON → Deny     (ML only)
↺ Reset → 💥 SWARM STRIKE → Deny     (coordinated)

PORT CONFLICT?
──────────────
--port 8003, 8004... → http://localhost:8003
```

---

*TARE AEGIS-ID — Setup & Run Guide*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: POC v3.5 — March 2026*
