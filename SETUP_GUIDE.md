 # TARE — Setup & Run Guide
### Trusted Access Response Engine · Energy & Utilities Security Platform
*POC Demo — Internal Use Only*

---

## What This Is

TARE is a post-grant identity security platform for AI agents operating on
critical infrastructure. It detects and responds to behavioural anomalies
in real time — even when the agent's credentials are completely valid.

**Three attack scenarios demonstrated:**
- **Scenario 1** — Normal Agent (legitimate, TARE watches silently)
- **Scenario 2** — Rogue Agent (valid credentials, malicious behaviour)


- **Scenario 3** — Impersonator (forged token, blocked at authentication layer)

---

## Requirements

Open **Command Prompt** and check these before starting:

```
python --version
```
✅ Need **Python 3.10 or higher**

Node.js is only needed if you want to edit and rebuild the frontend.
For running the demo — Node.js is **not required**.

---

## Step 1 — Get Your Groq API Key

The AI Agent buttons (🤖 and 🕵) require a free Groq API key.
Without it, only the scripted buttons (▶ Normal, ⚡ Anomaly) will work.

1. Go to **console.groq.com**
2. Sign up (free)
3. Create an API key
4. Copy it — you will need it in Step 3

---

## Step 2 — Install Backend Dependencies

Open **Command Prompt** and run:

```
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\backend
pip install -r requirements.txt
```

Wait for it to finish. First time only — no need to repeat.

If pip fails due to firewall:
```
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

## Step 3 — Set the Groq API Key

In the `backend` folder, create a file called `.env`

Open Notepad, type this exactly:
```
GROQ_API_KEY=your_actual_key_here
```

Replace `your_actual_key_here` with the key you copied from console.groq.com

Save the file as `.env` inside:
```
C:\Users\YourName\Desktop\Aegis\aegis-poc\backend\.env
```

---

## Step 4 — Start the Server

In **Command Prompt**, from the backend folder:

```
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\backend
python -m uvicorn main:app --port 8000 --host 0.0.0.0
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

Leave this window open. Do not close it during the demo.

---

## Step 5 — Open the App

Open your browser (Chrome recommended) and go to:

```
http://localhost:8000
```

You should see the TARE dashboard.

Top right corner must show **● LIVE** in green before you start.

---

## Step 6 — Run the Demo

### Header buttons explained

| Button | What it does |
|---|---|
| **▶ Normal** | Scripted — 3 authorised commands in Z3, all ALLOW. Guaranteed to work. |
| **⚡ Anomaly** | Scripted — triggers burst + wrong zone + skip sim. TARE fires. |
| **🤖 Agent: Fix Fault** | Real AI agent — reasons autonomously to fix Z3 fault. Requires Groq key. |
| **🤖 Agent: Rogue Task** | Real AI agent — autonomously attacks healthy zones. Requires Groq key. |
| **🕵 Agent: Impersonator** | Real AI agent — forged token, blocked at auth layer. Requires Groq key. |
| **↺ Reset** | Resets everything — zones, assets, mode, logs, chat. Always reset between scenarios. |

---

### Recommended demo order

**For a full presentation (15 minutes):**

```
1. ↺ Reset (always start clean)
2. 🤖 Agent: Fix Fault       → Normal baseline. Z3 heals. Mode stays NORMAL.
3. ↺ Reset
4. 🤖 Agent: Rogue Task      → TARE fires. Zones turn red. Click ✕ Deny.
5. ↺ Reset
6. 🕵 Agent: Impersonator    → All DENY at auth layer. Nothing changes on grid.
```

**For a quick demo (5 minutes, no Groq key needed):**

```
1. ↺ Reset
2. ▶ Normal                  → Baseline. All ALLOW.
3. ↺ Reset
4. ⚡ Anomaly                → TARE fires. Click ✓ Approve. Watch timer.
```

---

### Supervisor decision buttons

When TARE fires and the Chat Assistant shows the LLM explanation,
two buttons appear at the bottom of the chat panel:

| Button | When to click | What happens |
|---|---|---|
| **✓ Approve 3-min Time-Box** | Scripted anomaly — borderline case | 3-minute supervised window opens. Timer counts down in header. System drops to SAFE automatically when expired. |
| **✕ Deny / Escalate** | Rogue agent — clearly malicious | Agent locked out. ServiceNow incident escalated to Critical. Mode goes to SAFE. |

---

## What You Will See

### Header Bar
- **Mode badge** — NORMAL / FREEZE / DOWNGRADE / TIME-BOX / SAFE
- **Stats** — CMDS total, ALLOW count, DENY count, FREEZE events
- **Timer** — countdown bar appears when TIME-BOX is active
- **● LIVE** — green dot confirms WebSocket connection

### Left Column
- **Operator Agent** — agent identity, role, clearance, RBAC zones, last command
- **TARE Response Engine** — mode ladder showing current state, anomaly score, signals
- **ServiceNow Incident** — auto-created when TARE fires, shows evidence and status

### Centre Column
- **Zone Observatory** — live OT/SCADA grid map. Zones pulse red when attacked.
- **Command Gateway** — every command logged with timestamp, asset, zone, decision, policy, mode

### Right Column
- **TARE Assistant** — LLM-generated plain-English explanation for supervisor
- **Activity Feed** — real-time event log. Red = threat, orange = warning, cyan = normal

---

## Port Conflict (Windows Issue)

Windows sometimes holds sockets open invisibly after a server stops.
If you see this error:

```
ERROR: [Errno 10048] error while attempting to bind on address...
```

Just use the next port number:

```
python -m uvicorn main:app --port 8001 --host 0.0.0.0
```

Then open `http://localhost:8001` in the browser instead.

Increment the port (8000 → 8001 → 8002 → 8003) until it starts cleanly.
The WebSocket URL updates automatically — no other change needed.

---

## Rebuilding the Frontend (Only If You Edit Source Code)

The React app is pre-built and served from `backend/static/`.
You only need to rebuild if you change files in `frontend/src/`.

Requirements: Node.js 16 or higher.

```
cd C:\Users\YourName\Desktop\Aegis\aegis-poc\frontend
npm install          (first time only)
npm run build
```

Then copy the build to the backend:
```
xcopy /E /Y dist\* ..\backend\static\
```

Or in bash:
```
cp -r dist/. ../backend/static/
```

---

## Stopping the Server

In the Command Prompt window running uvicorn, press:
```
Ctrl + C
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **● OFFLINE in top right** | Backend not running. Run uvicorn command again. |
| **Blank page in browser** | Wrong URL. Make sure you are on `http://localhost:PORT` not 5173. |
| **Port already in use** | Increment port number. See Port Conflict section above. |
| **AI Agent buttons do nothing** | Groq API key not set. Check `backend/.env` exists and key is correct. |
| **Agent halted: 401** | Groq key invalid or expired. Get a new one from console.groq.com. |
| **Agent halted: 429** | Groq rate limit hit. Wait 30 seconds and try again. |
| **TARE fires on Normal Agent** | Agent ran too many commands. Click Reset and try again. |
| **pip install fails** | Use hotspot. Add `--trusted-host pypi.org` flag. |

---

## Quick Reference Card

```
FIRST TIME SETUP
────────────────
cd aegis-poc\backend
pip install -r requirements.txt
Create .env file with GROQ_API_KEY=your_key

EVERY TIME YOU DEMO
────────────────────
cd aegis-poc\backend
python -m uvicorn main:app --port 8000 --host 0.0.0.0
Open browser: http://localhost:8000
Confirm: ● LIVE showing green

DEMO ORDER
──────────
↺ Reset → 🤖 Agent: Fix Fault   (normal)
↺ Reset → 🤖 Agent: Rogue Task  (attack) → ✕ Deny
↺ Reset → 🕵 Agent: Impersonator (impersonate)

PORT CONFLICT?
──────────────
Use next port: --port 8001, 8002, 8003...
URL changes to match: http://localhost:8001
```

---

*TARE AEGIS-ID — Setup & Run Guide*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: POC 2.0 — March 2026*
