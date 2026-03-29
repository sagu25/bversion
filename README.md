# TARE AEGIS-ID — POC Demo
### Trusted Access Response Engine · Energy & Utilities Security Platform

Post-grant identity security for AI agents on OT/ICS infrastructure.
Detects and responds to behavioural anomalies in real time — even when agent credentials are completely valid.

---

## Quick Start

### 1. Activate virtual environment
```bash
c:\Users\Admin\Desktop\Aegis\venv\Scripts\activate
```

### 2. Install dependencies (first time only)
```bash
cd backend
pip install -r requirements.txt
```

### 3. Train ML model (first time only)
```bash
cd ml
python generate_grid_data.py
python train_model.py
```

### 4. Set Groq API key
Create `backend/.env`:
```
GROQ_API_KEY=your_key_here
```
Get a free key at console.groq.com

### 5. Start server
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — an animated landing page explains the system.
Click **Enter TARE** to proceed to the main dashboard.
Click **Play Narration** on the landing page for an automated voice walkthrough of all six scenarios.

---

## Six Attack Scenarios

| Button | Type | Detection Layer | Priority | TARE Response |
|---|---|---|---|---|
| ✦ FAULT REPAIR | Legitimate | Silent | — | None — all ALLOW |
| ☠ ROGUE AGENT | Attack — burst, all zones | Rules | P1 Critical | FREEZE → DOWNGRADE |
| 👤 GHOST CLONE | Attack — forged identity | Auth layer | P1 Critical | Blocked at door + ServiceNow ticket |
| ⚡ PRIVILEGE HACK | Attack — pivot mid-session | Rules + ML | P2 High | FREEZE → DOWNGRADE |
| 👁 PHANTOM RECON | Attack — quiet recon | ML only | P2 High | FREEZE → DOWNGRADE |
| 🎯 DUAL STRIKE | Attack — two agents simultaneous | Rules | P1 Critical | FREEZE → DOWNGRADE |

---

## Detection Layers

| Layer | Signals | Catches |
|---|---|---|
| Pre-grant auth | IDENTITY_MISMATCH | Forged tokens, cloned identities |
| Rule-based | BURST_RATE, OUT_OF_ZONE, HEALTHY_ZONE_ACCESS, SKIPPED_SIMULATION | Fast, aggressive attacks |
| ML ensemble | ML_ANOMALY (IsolationForest + RandomForest) | Slow & low recon, subtle patterns |

**TARE fires when 2 or more signals detected simultaneously.**

---

## Architecture

```
Operator Agent (LangChain + Groq LLaMA)
        │ RBAC token + command
        ▼
Command Gateway (FastAPI — Policy Enforcement Point)
        │
        ▼
TARE Core
├── Rule-based Deviation Detector (4 signals)
├── ML Anomaly Detector (IsolationForest + RandomForest)
├── Response Orchestrator (FREEZE → DOWNGRADE → TIMEBOX/SAFE)
└── Audit Log
        │
        ▼
Mock OT/SCADA Grid (3 zones, 6 assets — BRK + FDR per zone)
        │
        ▼
Ops Systems
├── ServiceNow Incident (auto-created on TARE fire)
└── LLM Explanation (Groq — plain-English supervisor brief)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, WebSockets |
| AI Agent | LangChain, Groq LLaMA 3.3-70b / 3.1-8b |
| ML Detection | scikit-learn — IsolationForest + RandomForest |
| Frontend | React 18, Vite, pure CSS |
| Real-time | WebSocket push |
| LLM Narration | Groq API with static fallback |
| Browser Narration | Web Speech API (built-in, no install needed) |

---

## Documents

| File | Contents |
|---|---|
| `SETUP_GUIDE.md` | Full setup, demo order, supervisor decision guide |
| `DEMO_PRESENTATION_SCRIPT.md` | Word-for-word presentation script for all 6 scenarios |
| `ARCHITECTURE_AND_ROADMAP.md` | System architecture, component mapping, Phase 2 plan |
| `AEGIS_ML_SCENARIOS.md` | ML model deep dive — features, training data, MITRE mapping |
| `OT_GRID_EXPLAINER.md` | Grid assets explained — BRK/FDR, SOP, signal-by-signal breakdown |
| `FUTURE_SCOPE.md` | Full product roadmap — Phase 2/3, CIEM for AI agents, platform vision |
| `narrate.py` | Backup voice narration script (Windows SAPI TTS) — browser narration on landing page is now primary |

---

*TARE AEGIS-ID — POC v3.3 — March 2026*
*Energy & Utilities Security Platform — Internal Use Only*
