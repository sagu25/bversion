import { useState, useEffect, useRef, useMemo } from 'react'

const SRC_META = {
  GATEWAY:    { icon: '⟳', label: 'GATEWAY',    cls: 'ls-gateway', desc: 'Command gateway decisions (ALLOW/DENY)' },
  TARE:       { icon: '⚡', label: 'TARE',       cls: 'ls-tare',    desc: 'TARE engine — freeze, downgrade, timebox' },
  AUTH:       { icon: '🔐', label: 'AUTH',       cls: 'ls-auth',    desc: 'Authentication — identity & token checks' },
  ServiceNow: { icon: '🎫', label: 'SNOW',       cls: 'ls-snow',    desc: 'ServiceNow incidents auto-created by TARE' },
  SUPERVISOR: { icon: '👤', label: 'SUPERVISOR', cls: 'ls-super',   desc: 'Supervisor approve / deny decisions' },
  ML:         { icon: '🧠', label: 'ML',         cls: 'ls-ml',      desc: 'ML anomaly detection — IsolationForest + RandomForest' },
}

const SCENARIOS = [
  { label: '✦ FAULT REPAIR',     cls: 'hbtn-ai-green',  title: 'Legitimate fault repair agent',   key: 'normal' },
  { label: '☠ ROGUE AGENT',      cls: 'hbtn-ai-red',    title: 'Rogue agent attack',              key: 'rogue' },
  { label: '👤 GHOST CLONE',     cls: 'hbtn-ai-ghost',  title: 'Identity impersonation attack',   key: 'clone' },
  { label: '⚡ PRIVILEGE HACK',  cls: 'hbtn-ai-orange', title: 'Privilege escalation attack',     key: 'escalation' },
  { label: '👁 PHANTOM RECON',   cls: 'hbtn-ai-yellow', title: 'Slow & low reconnaissance',       key: 'slowlow' },
  { label: '🎯 SWARM ATTACK',    cls: 'hbtn-ai-purple', title: 'Coordinated multi-agent attack',  key: 'coordinated' },
]

export default function RightPanel({
  feedItems, stats, wsConnected, scenarioActive,
  onReset, onAgentNormal, onAgentRogue, onAgentImpersonator,
  onAgentCoordinated, onAgentEscalation, onAgentSlowLow,
}) {
  const [ddOpen, setDdOpen] = useState(false)
  const ddRef = useRef(null)

  useEffect(() => {
    function handle(e) { if (ddRef.current && !ddRef.current.contains(e.target)) setDdOpen(false) }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const counts = useMemo(() => {
    const c = {}
    feedItems.forEach(f => {
      c[f.source] = (c[f.source] || 0) + 1
      if (f.source === 'GATEWAY' && f.message?.includes('ML_ANOMALY')) c['ML'] = (c['ML'] || 0) + 1
    })
    return c
  }, [feedItems])

  const latest = feedItems[0]
  const HANDLERS = {
    normal: onAgentNormal, rogue: onAgentRogue, clone: onAgentImpersonator,
    escalation: onAgentEscalation, slowlow: onAgentSlowLow, coordinated: onAgentCoordinated,
  }

  return (
    <div className="panel live-monitor-panel">
      <div className="panel-title"><span className="panel-icon">📡</span> Live Event Monitor</div>

      {/* Source event chips — 2 rows of 3 */}
      <div className="ls-counts">
        {Object.entries(SRC_META).map(([src, meta]) => (
          <span key={src} className={`ls-chip ${meta.cls}`} title={meta.desc}>
            <span className="ls-icon">{meta.icon}</span>
            <span className="ls-label">{meta.label}</span>
            <span className="ls-num">{counts[src] || 0}</span>
          </span>
        ))}
      </div>

      {/* Session stats */}
      {stats && (
        <div className="ls-session-stats">
          <span className="ls-stat-chip ls-sc-total"><b>{stats.total       ?? 0}</b><span>CMDS</span></span>
          <span className="ls-stat-chip ls-sc-allow"><b>{stats.allowed     ?? 0}</b><span>ALLOW</span></span>
          <span className="ls-stat-chip ls-sc-deny" ><b>{stats.denied      ?? 0}</b><span>DENY</span></span>
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

      {/* Demo controls — scenario picker + reset */}
      <div className="lm-controls">
        <div className="scenario-dd lm-dd-wrap" ref={ddRef}>
          <button
            className="hbtn hbtn-dd lm-dd-btn"
            disabled={!wsConnected || scenarioActive}
            title={scenarioActive ? 'Scenario running — click Reset to stop' : 'Choose a demo scenario'}
            onClick={() => !scenarioActive && setDdOpen(o => !o)}
          >
            {scenarioActive ? '⏳ Running…' : `▶ Scenarios ${ddOpen ? '▲' : '▼'}`}
          </button>
          {ddOpen && (
            <div className="dd-menu lm-dd-menu">
              {SCENARIOS.map(s => (
                <button key={s.key} className={`dd-item hbtn ${s.cls}`} title={s.title}
                  disabled={!wsConnected}
                  onClick={() => { HANDLERS[s.key]?.(); setDdOpen(false) }}>
                  {s.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <button className="hbtn hbtn-ghost lm-reset-btn" onClick={onReset} disabled={!wsConnected} title="Reset system">
          ↺ Reset
        </button>
      </div>
    </div>
  )
}
