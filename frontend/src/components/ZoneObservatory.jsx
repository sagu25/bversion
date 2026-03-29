import { ZONE_DISPLAY } from './ZoneInfoModal'


// Zone positions — Z3 top-centre, Z2 bottom-left, Z1 bottom-right
const ZONE_POS = {
  Z3: { cx: 290, cy: 90  },
  Z2: { cx:  80, cy: 228 },
  Z1: { cx: 500, cy: 228 },
}

// Only two links — Z3 feeds Z2 and Z1. No Z2→Z1 horizontal (removes extra arrow).
const LINKS = [
  { from:'Z3', to:'Z2', id:'l32' },
  { from:'Z3', to:'Z1', id:'l31' },
]

const ASSETS_BY_ZONE = {
  Z3: ['BRK-301','FDR-301'],
  Z2: ['BRK-205','FDR-205'],
  Z1: ['BRK-110','FDR-110'],
}

function zoneColor(zone, anomalyZones) {
  if (anomalyZones.includes(zone.id)) return { stroke:'#ff2d2d', fill:'rgba(255,45,45,0.12)', text:'#ff6b6b', glow:'drop-shadow(0 0 8px rgba(255,45,45,0.7))' }
  if (zone.health === 'FAULT')        return { stroke:'#ff8c00', fill:'rgba(255,140,0,0.1)',  text:'#ffa040', glow:'drop-shadow(0 0 8px rgba(255,140,0,0.5))' }
  return { stroke:'#00e87c', fill:'rgba(0,232,124,0.07)', text:'#00e87c', glow:'drop-shadow(0 0 6px rgba(0,232,124,0.4))' }
}

function stateColor(state) {
  if (state === 'OPEN' || state === 'RESTARTING') return '#ff8c00'
  if (state === 'CLOSED' || state === 'RUNNING')  return '#00e87c'
  return '#6b8fa3'
}

const THREAT_MODES = new Set(['FREEZE', 'DOWNGRADE', 'TIMEBOX_ACTIVE'])

export default function ZoneObservatory({ zones, assets, accessLog, mode, darkMode = true, onZoneClick }) {
  if (!zones || !assets) return null

  // Only show anomaly highlighting when TARE is actively in a threat mode
  const anomalyZones = THREAT_MODES.has(mode)
    ? (accessLog || []).filter(e => e.zone !== 'Z3').map(e => e.zone)
    : []

  const isAnomaly = anomalyZones.length > 0

  // Theme-aware SVG colors
  const svgBg     = darkMode ? '#060b14'            : '#d4dcf0'
  const dotColor  = darkMode ? '#1a2f4e'            : '#aab4d8'
  const zoneFill  = darkMode ? '#0a1525'            : '#e6eaf8'
  const chipFill  = darkMode ? 'rgba(14,29,53,0.9)' : 'rgba(220,228,248,0.96)'
  const labelText = darkMode ? '#2e5a8f'            : '#6070a8'

  return (
    <div className="panel zone-panel">
      <div className="panel-title">
        <span className="dot" />
        Zone Observatory · OT/SCADA Grid Map
        <span style={{ marginLeft:'auto', fontSize:'0.5rem', color:'var(--text-dim)', fontFamily:'var(--font-mono)' }}>
          REAL-TIME
        </span>
      </div>

      <div className="zone-svg-wrap">
        <svg viewBox="0 0 580 335" xmlns="http://www.w3.org/2000/svg">
          <defs>
            {/* Background dot-grid */}
            <pattern id="dotGrid" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="0.7" fill={dotColor} opacity="0.6" />
            </pattern>


            {/* Normal flow gradient */}
            <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stopColor="#00d4ff" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#00e87c" stopOpacity="0.6" />
            </linearGradient>

            {/* Attack gradient */}
            <linearGradient id="attackGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stopColor="#ff2d2d" stopOpacity="1" />
              <stop offset="100%" stopColor="#ff8c00" stopOpacity="0.7" />
            </linearGradient>

            {/* Arrow markers */}
            <marker id="arrowBlue" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto">
              <path d="M0,0.5 L0,5.5 L6,3 Z" fill="#00d4ff" />
            </marker>
            <marker id="arrowRed" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto">
              <path d="M0,0.5 L0,5.5 L6,3 Z" fill="#ff2d2d" />
            </marker>
          </defs>

          {/* Background */}
          <rect width="580" height="335" fill={svgBg} />
          <rect width="580" height="335" fill="url(#dotGrid)" />

          {/* Corner tags */}
          <text x="6" y="16" className="zone-lbl" style={{ textAnchor:'start', fontSize:'9px', fill: labelText }}>TARE GRID MAP</text>
          <text x="574" y="16" className="zone-lbl" style={{ textAnchor:'end', fontSize:'9px', fill: labelText }}>CLASSIFICATION: RESTRICTED</text>

          {/* Power lines between zones */}
          {LINKS.map(link => {
            const a = ZONE_POS[link.from]
            const b = ZONE_POS[link.to]
            const dx = b.cx - a.cx; const dy = b.cy - a.cy
            const len = Math.sqrt(dx*dx + dy*dy)
            const r = 54
            const x1 = a.cx + (dx/len)*r
            const y1 = a.cy + (dy/len)*r
            const x2 = b.cx - (dx/len)*r
            const y2 = b.cy - (dy/len)*r
            const isThreatLine = isAnomaly && (link.from !== 'Z2' || link.to !== 'Z1')
            return (
              <g key={link.id}>
                {/* Base line */}
                <line x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={isThreatLine ? 'url(#attackGrad)' : 'url(#flowGrad)'}
                  strokeWidth={isThreatLine ? 2 : 1.5}
                  strokeDasharray="10 5"
                  markerEnd={isThreatLine ? 'url(#arrowRed)' : 'url(#arrowBlue)'}
                  style={{
                    animation: 'flowDash 0.8s linear infinite',
                    strokeOpacity: isThreatLine ? undefined : 0.7,
                    ...(isThreatLine ? { animation: 'flowDash 0.3s linear infinite' } : {}),
                  }}
                />
              </g>
            )
          })}

          {/* Zone nodes */}
          {Object.values(zones).map(zone => {
            const pos  = ZONE_POS[zone.id]
            if (!pos) return null
            const col  = zoneColor(zone, anomalyZones)
            const isAttacked = anomalyZones.includes(zone.id)
            const zAssets = ASSETS_BY_ZONE[zone.id] || []

            return (
              <g key={zone.id}>
                {/* Outer glow ring */}
                <circle cx={pos.cx} cy={pos.cy} r={63}
                  fill={col.fill}
                  style={{ filter: col.glow, animation: isAttacked ? 'subPulse 0.5s ease-in-out infinite' : zone.health === 'FAULT' ? 'subPulse 2s ease-in-out infinite' : 'none' }}
                />
                {/* Zone circle base */}
                <circle cx={pos.cx} cy={pos.cy} r={50}
                  fill={zoneFill}
                  stroke={col.stroke}
                  strokeWidth={isAttacked ? 3 : 2}
                  style={{ transition: 'stroke 0.3s' }}
                />

{/* Zone ID — clickable */}
                <text x={pos.cx} y={pos.cy - 8} className="zone-id-lbl zone-id-clickable" fill={col.text}
                  onClick={() => onZoneClick?.(zone.id)}
                  style={{ cursor: 'pointer' }}>
                  {ZONE_DISPLAY[zone.id] || zone.id}
                </text>
                {/* Health */}
                <text x={pos.cx} y={pos.cy + 12} className="zone-hlth" fill={col.text} opacity={0.8}>
                  {zone.health === 'FAULT' ? '⚠ FAULT' : isAttacked ? '⚡ BREACHING' : '✓ HEALTHY'}
                </text>

                {/* Attack target badge */}
                {isAttacked && (
                  <g>
                    <rect x={pos.cx - 42} y={pos.cy - 78} width={84} height={16} rx={3}
                      fill="rgba(255,45,45,0.15)" stroke="rgba(255,45,45,0.6)" strokeWidth={1}
                      style={{ animation: 'subPulse 0.5s step-end infinite' }}
                    />
                    <text x={pos.cx} y={pos.cy - 66}
                      style={{ fontFamily:'var(--font-mono)', fontSize:'8.5px', fill:'#ff2d2d', fontWeight:700, textAnchor:'middle', letterSpacing:'0.1em' }}>
                      ANOMALY TARGET
                    </text>
                  </g>
                )}

                {/* Asset mini-chips — Z3 goes sideways, Z2/Z1 go below */}
                {zAssets.map((aid, i) => {
                  const ast = assets[aid]
                  if (!ast) return null
                  const isZ3 = zone.id === 'Z3'
                  const ax = isZ3
                    ? pos.cx + (i === 0 ? -115 : 115)  // left/right of Z3 — clear of glow ring
                    : pos.cx + (i === 0 ? -36 : 36)    // below Z2/Z1
                  const ay = isZ3 ? pos.cy : pos.cy + 82
                  return (
                    <g key={aid}>
                      <rect x={ax - 33} y={ay - 13} width={66} height={26} rx={4}
                        fill={chipFill} stroke={stateColor(ast.state)} strokeWidth={1.2} />
                      <text x={ax} y={ay - 2} className="asset-lbl">{aid}</text>
                      <text x={ax} y={ay + 9} className="asset-state" fill={stateColor(ast.state)}>{ast.state}</text>
                    </g>
                  )
                })}
              </g>
            )
          })}

          {/* "RBAC boundary" label */}
          <rect x={152} y={4} width={276} height={19} rx={4}
            fill="rgba(0,232,124,0.06)" stroke="rgba(0,232,124,0.25)" strokeWidth={1} />
          <text x={290} y={17}
            style={{ fontFamily:'var(--font-mono)', fontSize:'9.5px', fill:'#00e87c', fontWeight:700, textAnchor:'middle', letterSpacing:'0.08em' }}>
            ACTIVE TASK: Z3 · CLEARED: ALL ZONES
          </text>
        </svg>
      </div>
    </div>
  )
}
