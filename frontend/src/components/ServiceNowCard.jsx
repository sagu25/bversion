const SEV_COLOR = { HIGH: '#ff2d2d', CRITICAL: '#ff2d2d', MEDIUM: '#ff8c00', LOW: '#f59e0b' }

function fmtTs(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('en-GB', { hour12: false })
}

export default function ServiceNowCard({ incident }) {
  return (
    <div className={`panel snow-panel ${incident ? 'snow-active' : ''}`}>
      <div className="panel-title">
        <span className="panel-icon">🎫</span> ServiceNow Incident
        {incident && <span className="snow-badge">OPEN</span>}
      </div>

      {!incident ? (
        <div className="snow-empty">No active incident</div>
      ) : (
        <div className="snow-body">

          {/* Header row */}
          <div className="snow-row snow-id">
            {incident.incident_id}
            <span style={{ fontSize:'0.55rem', color:'var(--text-dim)', fontWeight:400 }}>
              {fmtTs(incident.created_at)}
            </span>
          </div>

          {/* Meta rows */}
          <div className="snow-row"><span>Priority</span><span className="snow-prio">{incident.priority}</span></div>
          <div className="snow-row"><span>Assigned</span><span>{incident.assigned_to}</span></div>
          <div className="snow-row"><span>Category</span><span>{incident.category}</span></div>
          <div className="snow-row"><span>State</span><span className="snow-state">{incident.state}</span></div>

          {/* Description */}
          <div className="snow-desc">{incident.short_description}</div>

          {/* Anomaly signals */}
          {(incident.evidence?.anomaly_signals?.length > 0) && (
            <div className="snow-section">
              <div className="snow-section-label">
                Deviation Signals
                <span className="snow-score">Score {incident.evidence.anomaly_score}</span>
              </div>
              <div className="snow-signals">
                {incident.evidence.anomaly_signals.map((s, i) => (
                  <span key={i} className="snow-sig-chip"
                    style={{ borderColor: `${SEV_COLOR[s.severity]}55`, color: SEV_COLOR[s.severity], background: `${SEV_COLOR[s.severity]}12` }}>
                    {s.signal}
                    <span style={{ opacity:0.7, marginLeft:3, fontWeight:400 }}>{s.severity}</span>
                  </span>
                ))}
              </div>
              {incident.evidence.anomaly_signals.map((s, i) => (
                <div key={i} className="snow-sig-detail">
                  <span style={{ color: SEV_COLOR[s.severity], marginRight:5 }}>▸</span>
                  {s.detail}
                </div>
              ))}
            </div>
          )}

          {/* Recent commands evidence */}
          {(incident.evidence?.recent_commands?.length > 0) && (
            <div className="snow-section">
              <div className="snow-section-label">Command Evidence</div>
              {incident.evidence.recent_commands.map((c, i) => (
                <div key={i} className="snow-cmd-row">
                  <span className="snow-cmd-name">{c.command}</span>
                  <span className="snow-cmd-asset">{c.asset_id}</span>
                  <span className="snow-cmd-zone">{c.zone}</span>
                </div>
              ))}
            </div>
          )}

          {/* Actions taken */}
          {(incident.evidence?.actions_taken?.length > 0) && (
            <div className="snow-section">
              <div className="snow-section-label">Actions Taken by TARE</div>
              {incident.evidence.actions_taken.map((a, i) => (
                <div key={i} className="snow-action-row">
                  <span className="snow-action-dot" />
                  {a}
                </div>
              ))}
            </div>
          )}

        </div>
      )}
    </div>
  )
}
