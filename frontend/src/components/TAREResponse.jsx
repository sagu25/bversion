const MODES = [
  { key:'NORMAL',        label:'Normal',        icon:'◉', desc:'Full access within RBAC policy' },
  { key:'FREEZE',        label:'Freeze',         icon:'❄', desc:'High-impact ops halted immediately' },
  { key:'DOWNGRADE',     label:'Downgrade',      icon:'▼', desc:'Read-only + diagnostics only' },
  { key:'TIMEBOX_ACTIVE',label:'Time-Box',       icon:'⏱', desc:'Switching re-enabled for 3 min' },
  { key:'SAFE',          label:'Safe',           icon:'✓', desc:'Constrained — awaiting operator review' },
]

const SIG_COLORS = {
  HIGH:     '#ef4444',
  CRITICAL: '#f97316',
  MEDIUM:   '#eab308',
}

export default function TAREResponse({ mode, signals, score }) {
  return (
    <div className="panel tare-panel">
      <div className="panel-title"><span className="panel-icon">⚡</span> TARE Response Engine</div>

      <div className="tare-inner">
        {/* Anomaly signals — shown at top when active */}
        {signals && signals.length > 0 && (
          <div className="signals-block">
            <div className="sig-header">
              Anomaly Score <span className="sig-score">{score}</span>/100
            </div>
            {signals.map((s, i) => (
              <div key={i} className="sig-row">
                <span className="sig-dot" style={{ background: SIG_COLORS[s.severity] || '#888' }} />
                <span className="sig-name">{s.signal}</span>
                <span className="sig-detail">{s.detail}</span>
              </div>
            ))}
          </div>
        )}

        {/* Mode ladder */}
        <div className="mode-ladder">
          {MODES.map((m, i) => {
            const isActive = m.key === mode
            const isPast   = MODES.findIndex(x => x.key === mode) > i
            return (
              <div key={m.key} className={`ladder-step ${isActive ? 'step-active' : ''} ${isPast ? 'step-past' : ''}`}>
                <div className="step-dot">{m.icon}</div>
                {i < MODES.length - 1 && <div className="step-line" />}
                <div className="step-body">
                  <div className="step-label">{m.label}</div>
                  <div className="step-desc">{m.desc}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
