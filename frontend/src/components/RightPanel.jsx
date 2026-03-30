import { useMemo, useState, useRef, useEffect } from 'react'
import { narrationEngine, narStart, narStop, narTogglePause, narToggleMute } from './LandingPage'

const SRC_META = {
  GATEWAY:    { icon: '⟳', label: 'GATEWAY',    cls: 'ls-gateway' },
  TARE:       { icon: '⚡', label: 'TARE',       cls: 'ls-tare'    },
  AUTH:       { icon: '🔐', label: 'AUTH',       cls: 'ls-auth'    },
  ServiceNow: { icon: '■',  label: 'SNOW',       cls: 'ls-snow'    },
  SUPERVISOR: { icon: '◆',  label: 'SUPERVISOR', cls: 'ls-super'   },
  ML:         { icon: '🤖', label: 'ML',         cls: 'ls-ml'      },
}

const SCENARIOS = [
  { label: '🟢 GRID DOCTOR',    key: 'normal',       title: 'Legitimate fault-repair agent' },
  { label: '🔴 GONE ROGUE',     key: 'rogue',        title: 'Rogue agent — burst attack across zones' },
  { label: '👻 GHOST CLONE',    key: 'impersonator', title: 'Forged identity — blocked at the door' },
  { label: '🔺 SCOPE CREEP',    key: 'escalation',   title: 'Starts legit, then grabs more zones' },
  { label: '🕳 SILENT RECON',   key: 'slowlow',      title: 'Slow & low — stays under the radar' },
  { label: '💥 SWARM STRIKE',   key: 'coordinated',  title: 'Two rogue agents hit simultaneously' },
]

export default function RightPanel({
  feedItems, stats, wsConnected, scenarioActive,
  onReset, onAgentNormal, onAgentRogue, onAgentImpersonator,
  onAgentCoordinated, onAgentEscalation, onAgentSlowLow,
}) {
  const [ddOpen, setDdOpen] = useState(false)
  const ddRef = useRef(null)
  const [narState, setNarState] = useState({
    playing: narrationEngine.playing,
    paused:  narrationEngine.paused,
    muted:   narrationEngine.muted,
  })

  useEffect(() => {
    const sync = () => setNarState({
      playing: narrationEngine.playing,
      paused:  narrationEngine.paused,
      muted:   narrationEngine.muted,
    })
    narrationEngine.listeners.push(sync)
    return () => { narrationEngine.listeners = narrationEngine.listeners.filter(f => f !== sync) }
  }, [])

  const counts = useMemo(() => {
    const c = {}
    feedItems.forEach(f => { c[f.source] = (c[f.source] || 0) + 1 })
    return c
  }, [feedItems])

  const latest = feedItems[0]

  const HANDLERS = {
    normal: onAgentNormal, rogue: onAgentRogue, impersonator: onAgentImpersonator,
    escalation: onAgentEscalation, slowlow: onAgentSlowLow, coordinated: onAgentCoordinated,
  }

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e) { if (ddRef.current && !ddRef.current.contains(e.target)) setDdOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const runScenario = (key) => {
    HANDLERS[key]?.()
    setDdOpen(false)
  }

  return (
    <div className="panel right-monitor-panel">
      <div className="panel-title">
        <span style={{ color:'var(--text-secondary)' }}>■</span>&nbsp;Live Event Monitor
      </div>

      {/* Source chips — 2 rows × 3 cols */}
      <div className="ls-source-grid">
        {Object.entries(SRC_META).map(([src, meta]) => (
          <span key={src} className={`ls-chip ${meta.cls}`}>
            <span className="ls-icon">{meta.icon}</span>
            <span className="ls-label">{meta.label}</span>
            <span className="ls-num">{counts[src] || 0}</span>
          </span>
        ))}
      </div>

      {/* Session stats */}
      {stats && (
        <div className="ls-session-stats">
          <span className="ls-stat-chip ls-sc-total"><b>{stats.total ?? 0}</b><span>CMDS</span></span>
          <span className="ls-stat-chip ls-sc-allow"><b>{stats.allowed ?? 0}</b><span>ALLOW</span></span>
          <span className="ls-stat-chip ls-sc-deny" ><b>{stats.denied ?? 0}</b><span>DENY</span></span>
          <span className="ls-stat-chip ls-sc-frz"  ><b>{stats.freeze_events ?? 0}</b><span>FRZ</span></span>
        </div>
      )}

      {/* Latest event */}
      <div className="ls-latest-wrap">
        <span className="ls-latest-label">LATEST</span>
        {latest ? (
          <div className="ls-latest">
            <span className="ls-latest-src">{latest.source}</span>
            <span className="ls-latest-msg">{latest.message}</span>
          </div>
        ) : (
          <div className="ls-latest"><span className="ls-latest-msg ls-dim">Awaiting events…</span></div>
        )}
      </div>

      <div style={{ flex:1 }} />

      {/* Narration controls */}
      <div className="rp-narration">
        <span className="rp-nar-label">🔈 NARRATION</span>
        <div className="rp-nar-btns">
          {!narState.playing && (
            <button className="rp-nar-btn" onClick={() => narStart(narrationEngine.index)} title="Start / Resume narration">▶ Start</button>
          )}
          {narState.playing && (
            <button className="rp-nar-btn" onClick={narTogglePause} title={narState.paused ? 'Resume' : 'Pause'}>
              {narState.paused ? '▶' : '⏸'}
            </button>
          )}
          {narState.playing && (
            <button className="rp-nar-btn rp-nar-stop" onClick={narStop} title="Stop">■</button>
          )}
          <button className={`rp-nar-btn ${narState.muted ? 'rp-nar-muted' : ''}`} onClick={narToggleMute} title={narState.muted ? 'Unmute' : 'Mute'}>
            {narState.muted ? '🔇' : '🔊'}
          </button>
        </div>
      </div>

      {/* Scenario dropdown + Reset */}
      <div className="rp-actions">

        {/* Scenarios dropdown */}
        <div className="rp-dd-wrap" ref={ddRef}>
          <button
            className={`rp-btn rp-btn-scenario ${ddOpen ? 'rp-btn-scenario-open' : ''}`}
            disabled={!wsConnected || scenarioActive}
            onClick={() => setDdOpen(o => !o)}
            title={scenarioActive ? 'Scenario running — Reset to stop' : 'Select a scenario'}
          >
            {scenarioActive ? '⏳ Running…' : `▶ Scenarios ${ddOpen ? '▲' : '▼'}`}
          </button>

          {ddOpen && (
            <div className="rp-dd-menu">
              {SCENARIOS.map(s => (
                <button
                  key={s.key}
                  className="rp-dd-item"
                  title={s.title}
                  onClick={() => runScenario(s.key)}
                >
                  {s.label}
                  <span className="rp-dd-desc">{s.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Reset */}
        <button className="rp-btn rp-btn-reset" onClick={onReset} disabled={!wsConnected}>
          ↺ Reset
        </button>
      </div>
    </div>
  )
}

export function LiveStatsBar() { return <div /> }
