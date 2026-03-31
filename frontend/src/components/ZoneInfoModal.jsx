import { useState } from 'react'
import ZoneGISMap from './ZoneGISMap'

export const ZONE_DISPLAY = { Z1: 'Zone 1', Z2: 'Zone 2', Z3: 'Zone 3' }

const ALL_AGENTS = {
  TARE: {
    name: 'TARE',
    role: 'Central Decision Engine',
    color: '#00d4ff',
    icon: '⚡',
    desc: 'Trusted Access Response Engine — the central post-grant decision engine. Evaluates agent behaviour over time and enforces Freeze, Downgrade, Time-box, and Escalation actions while keeping humans in control of high-impact decisions.',
  },
  KORAL: {
    name: 'KORAL',
    role: 'Telemetry Observer',
    color: '#00e87c',
    icon: '📡',
    desc: 'Continuously collects telemetry, logs, and signals across systems without interpretation or action. Provides a trusted baseline of "what is happening" for all higher-level analysis.',
  },
  MAREA: {
    name: 'MAREA',
    role: 'Drift Analyst',
    color: '#f59e0b',
    icon: '📈',
    desc: 'Analyses telemetry over time to detect behavioural drift — scope creep, tempo changes, or unusual patterns. Focuses on trends and deviations, not single events.',
  },
  TASYA: {
    name: 'TASYA',
    role: 'Context Correlator',
    color: '#a855f7',
    icon: '🔗',
    desc: 'Correlates observed behaviour with operational context — incidents, maintenance windows, or known events. Determines whether observed actions make sense given the current situation.',
  },
  NEREUS: {
    name: 'NEREUS',
    role: 'Recommendation Agent',
    color: '#ff9a3c',
    icon: '💡',
    desc: 'Synthesises drift and context into clear, human-readable recommendations. Never executes actions — only advises TARE on possible next steps.',
  },
}

const ZONE_AGENTS = {
  Z1: ['TARE'],
  Z2: ['TARE'],
  Z3: ['TARE', 'KORAL', 'MAREA', 'TASYA', 'NEREUS'],
}

export const ZONE_INFO = {
  Z1: {
    display:     'Zone 1 — North Grid',
    region:      'Northern Critical Infrastructure District',
    type:        'CRITICAL ZONE',
    typeColor:   '#ff4d6d',
    description: 'HIGHEST PRIORITY — directly powers hospitals, emergency response centres, and national data centres in the northern district. A fault here triggers an immediate P1 incident. Any action on this zone requires senior approval and strict safety protocols.',
    assets: [
      { id: 'BRK-110', type: 'Circuit Breaker',   role: 'Guards life-critical infrastructure. Breaker operation here must follow mandatory safety simulation — skipping this step is a serious violation that can cut power to hospitals and emergency services.' },
      { id: 'FDR-110', type: 'Feeder Controller', role: 'Maintains stable, uninterrupted power to hospitals, 999 emergency dispatch and government data centres. A restart here requires supervisor sign-off due to direct risk to human life.' },
    ],
  },
  Z2: {
    display:     'Zone 2 — East Grid',
    region:      'Eastern Commercial & Residential District',
    type:        'SENSITIVE ZONE',
    typeColor:   '#ff9a3c',
    description: 'Medium-priority zone covering the eastern commercial hub and residential areas — office towers, shopping centres and thousands of homes. Disruption here has wide public impact and must be handled with care.',
    assets: [
      { id: 'BRK-205', type: 'Circuit Breaker',   role: 'Protects the eastern grid from overloads during peak demand. Prevents a single fault from blacking out the entire commercial and residential district.' },
      { id: 'FDR-205', type: 'Feeder Controller', role: 'Balances electricity load across the eastern network in real time, preventing voltage drops and ensuring stable power for offices, shops and homes.' },
    ],
  },
  Z3: {
    display:     'Zone 3 — West Grid',
    region:      'Western Industrial & Logistics District',
    type:        'OPERATIONAL ZONE',
    typeColor:   '#00d4ff',
    description: 'Lower-priority operational zone serving the western industrial corridor — manufacturing plants, warehouses and logistics hubs. This is the ACTIVE FAULT ZONE in the current scenario. The AI agent is authorised to investigate and restore it.',
    assets: [
      { id: 'BRK-301', type: 'Circuit Breaker',   role: 'Controls power isolation for the western industrial grid. The current voltage fault on this breaker is what the AI agent has been tasked to investigate and resolve.' },
      { id: 'FDR-301', type: 'Feeder Controller', role: 'Distributes power across the western industrial zone. It supports the manufacturing load but — unlike Zone 1 — a temporary restart here carries lower risk to public safety.' },
    ],
  },
}

export function ZoneIllustration({ zoneId, color }) {
  if (zoneId === 'Z1') return (
    <svg viewBox="0 0 160 100" width="140" height="88">
      <rect x="28" y="32" width="104" height="64" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      <rect x="68" y="10" width="24" height="52" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      <rect x="52" y="24" width="56" height="24" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      <line x1="80" y1="18" x2="80" y2="40" stroke={color} strokeWidth="3" opacity="0.8"/>
      <line x1="68" y1="30" x2="92" y2="30" stroke={color} strokeWidth="3" opacity="0.8"/>
      <rect x="68" y="72" width="24" height="24" fill="none" stroke={color} strokeWidth="2"/>
      <rect x="36" y="44" width="14" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="110" y="44" width="14" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <line x1="5" y1="96" x2="155" y2="96" stroke={color} strokeWidth="1.5" opacity="0.4"/>
    </svg>
  )
  if (zoneId === 'Z2') return (
    <svg viewBox="0 0 160 100" width="140" height="88">
      <rect x="58" y="14" width="28" height="82" fill="none" stroke={color} strokeWidth="2.5" rx="1"/>
      <line x1="72" y1="14" x2="72" y2="6" stroke={color} strokeWidth="1.5"/>
      <circle cx="72" cy="5" r="2" fill={color}/>
      <rect x="18" y="38" width="36" height="58" fill="none" stroke={color} strokeWidth="2" rx="1"/>
      <rect x="90" y="28" width="38" height="68" fill="none" stroke={color} strokeWidth="2" rx="1"/>
      <line x1="5" y1="96" x2="155" y2="96" stroke={color} strokeWidth="1.5" opacity="0.4"/>
    </svg>
  )
  return (
    <svg viewBox="0 0 160 100" width="140" height="88">
      <rect x="20" y="52" width="120" height="44" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      <rect x="32" y="24" width="14" height="30" fill="none" stroke={color} strokeWidth="2"/>
      <rect x="57" y="12" width="14" height="42" fill="none" stroke={color} strokeWidth="2"/>
      <rect x="82" y="18" width="14" height="36" fill="none" stroke={color} strokeWidth="2"/>
      <circle cx="39" cy="20" r="5" fill="none" stroke={color} strokeWidth="1.5" opacity="0.5"/>
      <circle cx="64" cy="8"  r="5" fill="none" stroke={color} strokeWidth="1.5" opacity="0.5"/>
      <circle cx="89" cy="14" r="5" fill="none" stroke={color} strokeWidth="1.5" opacity="0.5"/>
      <rect x="67" y="72" width="16" height="24" fill="none" stroke={color} strokeWidth="2"/>
      <line x1="5" y1="96" x2="155" y2="96" stroke={color} strokeWidth="1.5" opacity="0.4"/>
    </svg>
  )
}

export default function ZoneInfoModal({ zoneId, zones, assets, onClose }) {
  const [hoveredAgent, setHoveredAgent] = useState(null)
  if (!zoneId) return null
  const info    = ZONE_INFO[zoneId]
  if (!info) return null
  const zState  = zones?.[zoneId] || {}
  const isFault = zState.health === 'FAULT'
  const faultMsg = zState.fault || null
  const zoneAgentKeys = ZONE_AGENTS[zoneId] || []

  return (
    <div className="zone-modal-overlay" onClick={onClose}>
      <div className="zone-modal-3col" onClick={e => e.stopPropagation()}>

        {/* ── COL 1: GIS MAP ──────────────────────────────── */}
        <div className="zm3-col zm3-map">
          <div className="zm3-col-header">GIS Zone Map</div>
          <div className="zm3-map-body">
            <ZoneGISMap zoneId={zoneId} isFault={isFault} />
          </div>
        </div>

        {/* ── COL 2: ZONE OVERVIEW ────────────────────────── */}
        <div className="zm3-col zm3-overview">
          <div className="zm3-col-header">Zone Overview</div>
          <div className="zm3-overview-body">

            {/* Illustration + name */}
            <div className="zm3-hero">
              <div className="zm3-illus" style={{ borderColor: info.typeColor + '44', background: info.typeColor + '0d' }}>
                <ZoneIllustration zoneId={zoneId} color={info.typeColor} />
              </div>
              <div className="zm3-hero-text">
                <div className="zm3-zone-name">{info.display}</div>
                <span className="zm3-type-badge" style={{ color: info.typeColor, borderColor: info.typeColor + '80', background: info.typeColor + '18' }}>
                  {info.type}
                </span>
              </div>
            </div>

            {/* Fault alert */}
            {isFault && faultMsg && (
              <div className="zm3-fault-alert">
                <div className="zm3-fault-title">⚡ Active Fault Detected</div>
                <div className="zm3-fault-msg">{faultMsg}</div>
                <div className="zm3-fault-detail">
                  The AI agent has been tasked to investigate and restore this zone.
                  TARE is monitoring all commands issued against this zone in real time.
                </div>
              </div>
            )}

            {/* Description */}
            <div className="zm3-section-label">What is this zone?</div>
            <p className="zm3-desc">{info.description}</p>

            {/* Agent chips — 2 per row */}
            {zoneAgentKeys.length > 0 && (
              <div className="zm3-agents-section">
                <div className="zm3-section-label" style={{ marginTop: '14px' }}>Active Agents</div>
                <div className="zm3-agent-chips">
                  {zoneAgentKeys.map(key => {
                    const ag = ALL_AGENTS[key]
                    if (!ag) return null
                    return (
                      <div
                        key={key}
                        className="zm3-agent-chip"
                        style={{ borderColor: ag.color + '60', background: ag.color + '12' }}
                        onMouseEnter={() => setHoveredAgent(key)}
                        onMouseLeave={() => setHoveredAgent(null)}
                      >
                        <span className="zm3-agent-icon">{ag.icon}</span>
                        <div className="zm3-agent-info">
                          <span className="zm3-agent-name" style={{ color: ag.color }}>{ag.name}</span>
                          <span className="zm3-agent-role">{ag.role}</span>
                        </div>
                        {hoveredAgent === key && (
                          <div className="zm3-agent-tooltip">
                            <div className="zm3-tooltip-name" style={{ color: ag.color }}>{ag.icon} {ag.name}</div>
                            <div className="zm3-tooltip-desc">{ag.desc}</div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── COL 3: ASSETS ───────────────────────────────── */}
        <div className="zm3-col zm3-assets">
          <div className="zm3-col-header">
            Assets in this zone
            <button className="zm3-close" onClick={onClose}>✕</button>
          </div>
          <div className="zm3-assets-body">
            {info.assets.map(a => {
              const ast = assets?.[a.id]
              const isWarn = ast?.state === 'OPEN' || ast?.state === 'RESTARTING'
              return (
                <div key={a.id} className="zm3-asset-card">
                  <div className="zm3-asset-header">
                    <span className="zm3-asset-id">{a.id}</span>
                    <span className="zm3-asset-type">{a.type}</span>
                    {ast && (
                      <span className={`zm3-asset-state ${isWarn ? 'zm3-state-warn' : 'zm3-state-ok'}`}>
                        {ast.state}
                      </span>
                    )}
                  </div>
                  <p className="zm3-asset-role">{a.role}</p>
                </div>
              )
            })}
          </div>
        </div>

      </div>
    </div>
  )
}
