"""
TARE — Trusted Access Response Engine
FastAPI backend with WebSocket push and REST demo commands
"""
import asyncio
import json
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from tare_engine import TAREEngine
from grid_agent import (run_normal_agent, run_rogue_agent, run_impersonator_agent,
                        run_coordinated_agent, run_escalation_agent, run_slow_low_agent,
                        run_readonly_write_agent)
from mcp_server import router as mcp_router

import os
try:
    from groq import Groq as _Groq
    _chat_groq = _Groq(api_key=os.environ.get("GROQ_API_KEY", "")) if os.environ.get("GROQ_API_KEY") else None
except Exception:
    _chat_groq = None

# ─── WebSocket connection manager ──────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop):
        self._loop = loop

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def sync_broadcast(self, data: dict):
        """Called from engine threads — schedules broadcast on the event loop."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.broadcast(data), self._loop)


manager = ConnectionManager()
engine  = TAREEngine(broadcast_fn=manager.sync_broadcast)

# ─── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.set_loop(asyncio.get_event_loop())
    yield

app = FastAPI(title="TARE — Trusted Access Response Engine", lifespan=lifespan)
app.state.tare_engine = engine

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_router)

# ─── WebSocket endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_json(engine._snapshot())
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)

# ─── Demo / control endpoints ──────────────────────────────────────────────────
@app.post("/demo/normal")
async def demo_normal():
    engine.run_normal_ops()
    return {"status": "started"}

@app.post("/demo/anomaly")
async def demo_anomaly():
    engine.trigger_anomaly()
    return {"status": "started"}

# ─── Real AI Agent endpoints ───────────────────────────────────────────────────
@app.post("/agent/normal")
async def agent_normal():
    """Start the real LangChain agent with the legitimate fault-repair task."""
    run_normal_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "normal"}

@app.post("/agent/rogue")
async def agent_rogue():
    """Start the real LangChain agent with the rogue/malicious task."""
    run_rogue_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "rogue"}

@app.post("/agent/impersonator")
async def agent_impersonator():
    """Start the impersonator agent — forged token, blocked at auth layer."""
    run_impersonator_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "impersonator"}

@app.post("/agent/coordinated")
async def agent_coordinated():
    """Two rogue agents hit Z1 and Z2 simultaneously."""
    run_coordinated_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "coordinated"}

@app.post("/agent/escalation")
async def agent_escalation():
    """Starts normal in Z3, escalates to all zones mid-session."""
    run_escalation_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "escalation"}

@app.post("/agent/slowlow")
async def agent_slowlow():
    """Slow & low recon — rules silent, ML model flags it."""
    run_slow_low_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "slowlow"}

@app.post("/agent/readonly-write")
async def agent_readonly_write():
    """Read-only identity attempts a write operation — KORAL logs, TARE checks policy, BARRIER enforces."""
    run_readonly_write_agent(engine, manager.sync_broadcast)
    return {"status": "agent_started", "task": "readonly_write"}

@app.post("/approve/timebox")
async def approve_timebox():
    engine.approve_timebox(duration_minutes=3)
    return {"status": "approved"}

@app.post("/deny/timebox")
async def deny_timebox():
    engine.deny_timebox()
    return {"status": "denied"}

@app.post("/reset")
async def reset():
    engine.reset()
    return {"status": "reset"}

# ─── Historical context (simulated audit trail for demo) ──────────────────────
HISTORICAL_SUMMARY = """
Past 30 days audit data for TARE AEGIS-ID platform (Blueverse Energy Grid):
- Total commands processed: 847 | Allowed: 791 | Blocked: 56 | Freeze events: 18
- Rogue/burst-rate incidents: 11 (8 on Zone 1 hospital grid, 3 Zone 2 pivots) — all frozen within 4 seconds
- Scope creep incidents: 7 — agents starting in Zone 3 then expanding to Zone 1/Zone 2
- Identity mismatch (forged tokens): 5 — all blocked before any command executed
- ML anomaly detections: 9 — slow & low recon patterns caught over 10-40 min windows
- Coordinated swarm attacks: 3 — multiple agents attacking simultaneously, all frozen in parallel
- ServiceNow incidents raised: 14 (9 P1 Critical, 4 P2 High, 1 P3 Medium)
- Mean time to containment: 6.1 minutes
- Zone 1 (North Grid — Critical, hospitals/emergency): 23 unauthorised access attempts
- Zone 2 (East Grid — Commercial/Residential): 17 unauthorised access attempts
- Zone 3 (West Grid — Operational): authorised zone, no policy violations
- 6 distinct agent IDs flagged: 2 compromised (credentials revoked), 3 mis-configured, 1 under investigation
- No critical infrastructure was impacted — all threats contained before asset changes
"""

def _is_historical(q: str) -> bool:
    time_words = ["past", "last", "days", "weeks", "months", "30 day", "15 day", "7 day",
                  "this week", "this month", "yesterday", "history", "historical",
                  "over time", "trend", "total so far", "so far", "till now", "until now", "recently"]
    return any(w in q for w in time_words)

def _build_session_context(snap: dict) -> str:
    stats       = snap.get("stats", {})
    gateway_log = snap.get("gateway_log", [])
    incident    = snap.get("active_incident")
    agent       = snap.get("agent", {})
    mode        = snap.get("mode", "NORMAL")

    rogue_count       = sum(1 for e in gateway_log if any(s.get("signal") in ("BURST_RATE","OUT_OF_ZONE") for s in e.get("signals", [])))
    scope_creep_count = sum(1 for e in gateway_log if any(s.get("signal") == "HEALTHY_ZONE_ACCESS" for s in e.get("signals", [])))
    identity_count    = sum(1 for e in gateway_log if any(s.get("signal") == "IDENTITY_MISMATCH" for s in e.get("signals", [])))
    ml_count          = sum(1 for e in gateway_log if any(s.get("signal") == "ML_ANOMALY" for s in e.get("signals", [])))

    zone_hits = {}
    for e in gateway_log:
        z = e.get("zone") or (e.get("asset_id","")[:2] if e.get("asset_id") else "")
        if z: zone_hits[z] = zone_hits.get(z, 0) + 1
    zone_str = ", ".join(f"{k}: {v} cmd(s)" for k, v in sorted(zone_hits.items())) or "none yet"

    recent_cmds = gateway_log[-5:] if gateway_log else []
    recent_str  = "\n".join(
        f"  - {e.get('command')} on {e.get('asset_id')} in {e.get('zone')} → {e.get('decision')} ({e.get('reason','')})"
        for e in recent_cmds
    ) or "  none"

    inc_str = "None"
    if incident:
        inc_str = (f"{incident.get('incident_id')} | Priority {incident.get('priority')} | "
                   f"State: {incident.get('state')} | Assigned: {incident.get('assigned_to')}")

    return f"""
Current session data:
- Agent: {agent.get('name','unknown')} (ID: {agent.get('id','?')}, Clearance: {agent.get('clearance','?')}, Authorised zones: {agent.get('rbac_zones','?')})
- TARE mode: {mode}
- Commands: total={stats.get('total',0)}, allowed={stats.get('allowed',0)}, blocked={stats.get('denied',0)}, freeze_events={stats.get('freeze_events',0)}
- Signals fired: rogue/burst={rogue_count}, scope_creep={scope_creep_count}, identity_mismatch={identity_count}, ml_anomaly={ml_count}
- Zone activity: {zone_str}
- Active ServiceNow incident: {inc_str}
- Last 5 commands:
{recent_str}
"""

# ─── TARE Assistant chat query — LLM powered ─────────────────────────────────
@app.post("/chat/query")
async def chat_query(body: dict):
    question = (body.get("question") or "").strip()
    if not question:
        return JSONResponse({"answer": "Please ask a question."})

    snap = engine._snapshot()
    hist = _is_historical(question.lower())

    # Build context for the LLM
    session_ctx  = _build_session_context(snap)
    hist_ctx     = HISTORICAL_SUMMARY if hist else ""

    system_prompt = """You are TARE — Trusted Access Response Engine. You speak in first person, directly to the supervisor, like a sharp analyst who is on top of everything happening on the grid right now.

Never write like a system generating a report. Speak like a person. Use "I", "I caught", "I froze", "you approved", "the agent tried". Be specific with zones, commands and numbers when available. If you don't know something from the context, say "I don't have that in the session data" — don't make anything up.

Keep answers conversational and under 3-4 sentences unless a detailed breakdown is explicitly asked for."""

    user_prompt = f"""
{f"30-day historical audit data:{hist_ctx}" if hist_ctx else ""}
Live session data:{session_ctx}

Supervisor question: {question}
"""

    # Try LLM first
    if _chat_groq:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                resp = _chat_groq.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    max_tokens=220,
                    temperature=0.3,
                )
                return JSONResponse({"answer": resp.choices[0].message.content.strip()})
            except Exception as e:
                if "429" in str(e):
                    import time; time.sleep(2); continue
                break

    # Fallback if LLM unavailable
    stats = snap.get("stats", {})
    return JSONResponse({"answer": (
        f"Session summary — Total: {stats.get('total',0)} commands | "
        f"Allowed: {stats.get('allowed',0)} | Blocked: {stats.get('denied',0)} | "
        f"Freeze events: {stats.get('freeze_events',0)}. "
        f"(LLM unavailable — check GROQ_API_KEY in .env)"
    )})

# ─── Audit log download ────────────────────────────────────────────────────────
@app.get("/logs/download")
async def download_logs():
    snap = engine._snapshot()
    log_lines = [json.dumps(e) for e in snap.get("gateway_log", [])]
    return JSONResponse({"log": "\n".join(log_lines), "entries": len(log_lines)})

# ─── Static files (React build) ────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = STATIC_DIR / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(STATIC_DIR / "index.html")
