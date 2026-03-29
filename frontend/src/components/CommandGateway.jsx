import { useState, useRef } from 'react'
import { ZONE_DISPLAY, ZONE_INFO, ZoneIllustration } from './ZoneInfoModal'

const DEC_CLS = { ALLOW:'dec-allow', DENY:'dec-deny' }

function fmtTs(ts) {
  if (!ts) return ''
  return ts.slice(11, 19)
}

function ZoneHoverTooltip({ zone, anchorRect }) {
  if (!zone || !anchorRect) return null
  const info = ZONE_INFO[zone]
  if (!info) return null

  // Position: prefer above the element, fall back to below if near top of screen
  const TOOLTIP_H = 210
  const TOOLTIP_W = 230
  const above = anchorRect.top > TOOLTIP_H + 20
  const top   = above
    ? anchorRect.top  - TOOLTIP_H - 8
    : anchorRect.bottom + 8
  const left  = Math.min(anchorRect.left, window.innerWidth - TOOLTIP_W - 12)

  return (
    <div
      className="zone-hover-tooltip"
      style={{ top, left, width: TOOLTIP_W }}
    >
      {/* Illustration */}
      <div className="zht-illustration" style={{ borderBottomColor: info.typeColor + '40' }}>
        <ZoneIllustration zoneId={zone} color={info.typeColor} />
      </div>

      {/* Info */}
      <div className="zht-body">
        <div className="zht-name">{info.display}</div>
        <span className="zht-type" style={{ color: info.typeColor, borderColor: info.typeColor + '60', background: info.typeColor + '18' }}>
          {info.type}
        </span>
        <p className="zht-desc">{info.description.slice(0, 120)}…</p>
        <div className="zht-hint">Click for full details</div>
      </div>
    </div>
  )
}

export default function CommandGateway({ log, onZoneClick }) {
  const [tooltip, setTooltip] = useState(null)   // { zone, rect }
  const leaveTimer = useRef(null)

  function handleEnter(e, zone) {
    clearTimeout(leaveTimer.current)
    const rect = e.currentTarget.getBoundingClientRect()
    setTooltip({ zone, rect })
  }

  function handleLeave() {
    // Small delay so cursor can reach tooltip without it vanishing
    leaveTimer.current = setTimeout(() => setTooltip(null), 120)
  }

  return (
    <div className="panel gw-panel">
      <div className="panel-title"><span className="panel-icon">🛡</span> Command Gateway (PEP)</div>

      {/* Hover tooltip — rendered outside table to avoid clipping */}
      <ZoneHoverTooltip
        zone={tooltip?.zone}
        anchorRect={tooltip?.rect}
      />

      {(!log || log.length === 0) ? (
        <div className="gw-empty">Awaiting commands…</div>
      ) : (
        <div className="gw-table-wrap">
          <table className="gw-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Command</th>
                <th>Asset</th>
                <th>Zone</th>
                <th>Decision</th>
                <th>Policy</th>
                <th>Mode</th>
              </tr>
            </thead>
            <tbody>
              {log.map(e => (
                <tr key={e.id} className={e.signals?.length ? 'row-anomaly' : ''}>
                  <td className="gw-ts">{fmtTs(e.ts)}</td>
                  <td className="gw-cmd">{e.command}</td>
                  <td className="gw-asset">{e.asset_id}</td>
                  <td>
                    <button
                      className="gw-zone-btn"
                      onClick={() => onZoneClick?.(e.zone)}
                      onMouseEnter={ev => handleEnter(ev, e.zone)}
                      onMouseLeave={handleLeave}
                      title="Hover to preview · Click for details"
                    >
                      {ZONE_DISPLAY[e.zone] || e.zone}
                      <span className="gw-zone-hint">ℹ</span>
                    </button>
                  </td>
                  <td><span className={`dec-badge ${DEC_CLS[e.decision]}`}>{e.decision}</span></td>
                  <td className="gw-policy">{e.policy}</td>
                  <td className="gw-mode">{e.mode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
