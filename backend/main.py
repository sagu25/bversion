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
                        run_coordinated_agent, run_escalation_agent, run_slow_low_agent)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
