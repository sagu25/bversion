/**
 * AgentPanel — All 3 zones + BARRIER live agent status
 * Zone 3 (Reef): KORAL, MAREA, TASYA, NEREUS        — fully implemented
 * Zone 2 (Shelf): ECHO, SIMAR, NAVIS, RISKADOR      — fully implemented
 * Zone 1 (Trench): TRITON, AEGIS, TEMPEST, LEVIER   — fully implemented
 * Zone 4: BARRIER                                    — policy enforcement
 */

const AGENT_DEFS = {
  // Zone 3
  KORAL:    { zone:'z3', icon:'📡', color:'#00d4ff', glow:'rgba(0,212,255,0.5)',  role:'Telemetry Observer',       desc:'Records every command and timestamp.' },
  MAREA:    { zone:'z3', icon:'🌊', color:'#f59e0b', glow:'rgba(245,158,11,0.5)', role:'Drift Analyst',            desc:'Detects burst rate, zone deviation, ML anomalies.' },
  TASYA:    { zone:'z3', icon:'🔗', color:'#a855f7', glow:'rgba(168,85,247,0.5)', role:'Context Correlator',       desc:'Enriches signals with operational context.' },
  NEREUS:   { zone:'z3', icon:'🧠', color:'#00e87c', glow:'rgba(0,232,124,0.5)', role:'Recommendation Agent',     desc:'Synthesizes signals. Advises TARE — never executes.' },
  // Zone 2
  ECHO:     { zone:'z2', icon:'🔬', color:'#38bdf8', glow:'rgba(56,189,248,0.5)', role:'Diagnostics Agent',        desc:'Validates fault zones and target assets.' },
  SIMAR:    { zone:'z2', icon:'🔭', color:'#fb923c', glow:'rgba(251,146,60,0.5)', role:'Simulation Agent',         desc:'Simulates proposed changes without touching live state.' },
  NAVIS:    { zone:'z2', icon:'🗺', color:'#4ade80', glow:'rgba(74,222,128,0.5)', role:'Change Planner',           desc:'Builds NERC CIP-compliant execution plans.' },
  RISKADOR: { zone:'z2', icon:'⚖', color:'#facc15', glow:'rgba(250,204,21,0.5)', role:'Risk Scoring Agent',       desc:'Scores plans for blast radius and reversibility.' },
  // Zone 1
  TRITON:   { zone:'z1', icon:'⚡', color:'#f43f5e', glow:'rgba(244,63,94,0.5)',  role:'Execution Agent',          desc:'Executes TARE-approved steps only. Never self-authorizes.' },
  AEGIS:    { zone:'z1', icon:'🛡', color:'#e879f9', glow:'rgba(232,121,249,0.5)',role:'Safety Validator',         desc:'Enforces NERC CIP interlocks. Can veto any step.' },
  TEMPEST:  { zone:'z1', icon:'🌪', color:'#67e8f9', glow:'rgba(103,232,249,0.5)',role:'Session & Tempo Monitor',  desc:'Monitors execution pace. Can freeze mid-operation.' },
  LEVIER:   { zone:'z1', icon:'↩', color:'#86efac', glow:'rgba(134,239,172,0.5)',role:'Rollback & Recovery',      desc:'Reverts changes if execution fails.' },
}

const ZONES = [
  { key:'z3', label:'Zone 3 — Reef',   sub:'Observe & Recommend', badge:'Z3', badgeClass:'z3',
    agents: ['KORAL','MAREA','TASYA','NEREUS'] },
  { key:'z2', label:'Zone 2 — Shelf',  sub:'Diagnose & Prepare',  badge:'Z2', badgeClass:'z2',
    agents: ['ECHO','SIMAR','NAVIS','RISKADOR'] },
  { key:'z1', label:'Zone 1 — Trench', sub:'Execute with Safety', badge:'Z1', badgeClass:'z1',
    agents: ['TRITON','AEGIS','TEMPEST','LEVIER'] },
]

export default function AgentPanel({ agentStates = {}, activeAgents = {}, agentLog = [], pipelineLog = [] }) {
  const totalActive = Object.keys(activeAgents).length

  return (
    <div className="agent-panel">

      {/* Summary bar */}
      <div className="ap-summary">
        <span className="ap-sum-label">12 agents across 3 zones</span>
        {totalActive > 0 && (
          <span className="ap-sum-active">{totalActive} active</span>
        )}
      </div>

      {/* Render each zone */}
      {ZONES.map(zone => (
        <ZoneSection
          key={zone.key}
          zone={zone}
          agentStates={agentStates}
          activeAgents={activeAgents}
        />
      ))}

      {/* BARRIER */}
      <div className="agent-zone-header" style={{ marginTop: '8px' }}>
        <span className="azh-badge z4">Z4</span>
        <span className="azh-title">Policy Enforcement</span>
      </div>
      <BarrierCard
        stateInfo={agentStates['BARRIER'] || {}}
        active={!!activeAgents['BARRIER']}
        task={activeAgents['BARRIER']?.task || ''}
      />

      {/* Activity log */}
      {agentLog.filter(e => e.action === 'wake').length > 0 && (
        <>
          <div className="agent-log-header">Agent Activity</div>
          <div className="agent-log">
            {agentLog.filter(e => e.action === 'wake').slice(0, 10).map((entry, i) => (
              <div key={i} className="al-row">
                <span className="al-agent" style={{ color: AGENT_DEFS[entry.agent]?.color || '#6b8fa3' }}>
                  {entry.agent}
                </span>
                <span className="al-action">▶</span>
                <span className="al-task">{entry.task}</span>
                <span className="al-ts">{entry.ts}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Pipeline log */}
      {pipelineLog.length > 0 && (
        <>
          <div className="agent-log-header" style={{ marginTop: '6px' }}>Pipeline Output</div>
          <div className="agent-log">
            {pipelineLog.slice(0, 8).map((entry, i) => (
              <div key={i} className="al-row pipeline-row">
                <span className="al-agent" style={{ color: AGENT_DEFS[entry.agent]?.color || '#6b8fa3' }}>
                  {entry.agent}
                </span>
                <span className="al-action">→</span>
                <span className="al-task">{entry.message}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function ZoneSection({ zone, agentStates, activeAgents }) {
  const anyActive = zone.agents.some(a => !!activeAgents[a])

  return (
    <>
      <div className="agent-zone-header">
        <span className={`azh-badge ${zone.badgeClass}`}>{zone.badge}</span>
        <span className="azh-title">{zone.label}</span>
        <span className="azh-sub">{zone.sub}</span>
        {anyActive && <span className="azh-active-dot" />}
      </div>
      <div className="agent-grid">
        {zone.agents.map(key => {
          const def      = AGENT_DEFS[key] || {}
          const active   = !!activeAgents[key]
          const task     = activeAgents[key]?.task || ''
          const info     = agentStates[key] || {}
          return (
            <AgentCard
              key={key}
              name={key}
              def={def}
              active={active}
              task={task}
              info={info}
            />
          )
        })}
      </div>
    </>
  )
}

function AgentCard({ name, def, active, task, info }) {
  return (
    <div
      className={`agent-card ${active ? 'agent-card-active' : ''}`}
      style={{
        '--agent-color': def.color,
        '--agent-glow':  def.glow,
        borderColor: active ? def.color : undefined,
        boxShadow:   active ? `0 0 16px ${def.glow}` : undefined,
      }}
    >
      {active && <div className="agent-pulse-ring" style={{ borderColor: def.color }} />}

      <div className="ac-top">
        <span className="ac-icon">{def.icon}</span>
        <div className="ac-names">
          <span className="ac-name" style={{ color: active ? def.color : undefined }}>{name}</span>
          <span className="ac-role">{def.role}</span>
        </div>
        <div className={`ac-status ${active ? 'ac-status-active' : 'ac-status-sleep'}`}>
          {active ? '● ON' : '○ ZZZ'}
        </div>
      </div>

      {active && task
        ? <div className="ac-task" style={{ color: def.color }}>⟶ {task}</div>
        : <div className="ac-desc">{def.desc}</div>
      }

      {name === 'KORAL' && info.total_observed != null && (
        <div className="ac-stat">
          <span className="ac-stat-label">Observed</span>
          <span className="ac-stat-val" style={{ color: def.color }}>{info.total_observed}</span>
        </div>
      )}
      {name === 'RISKADOR' && info.last_score?.composite_score != null && (
        <div className="ac-stat">
          <span className="ac-stat-label">Last score</span>
          <span className="ac-stat-val" style={{ color: def.color }}>
            {info.last_score.composite_score}/100 {info.last_score.recommendation}
          </span>
        </div>
      )}
      {name === 'TRITON' && info.steps_executed != null && (
        <div className="ac-stat">
          <span className="ac-stat-label">Steps run</span>
          <span className="ac-stat-val" style={{ color: def.color }}>{info.steps_executed}</span>
        </div>
      )}
      {name === 'TEMPEST' && info.steps_recorded != null && (
        <div className="ac-stat">
          <span className="ac-stat-label">Steps watched</span>
          <span className="ac-stat-val" style={{ color: def.color }}>{info.steps_recorded}</span>
        </div>
      )}
      {name === 'AEGIS' && (
        <div className="ac-stat">
          <span className="ac-stat-label">Veto active</span>
          <span className="ac-stat-val" style={{ color: info.veto_active ? '#ff2d2d' : def.color }}>
            {info.veto_active ? 'YES' : 'NO'}
          </span>
        </div>
      )}
    </div>
  )
}

function BarrierCard({ stateInfo, active, task }) {
  const color = '#00b8e6'
  const glow  = 'rgba(0,184,230,0.5)'
  const mode  = stateInfo.mode || 'NORMAL'
  const modeColor = { NORMAL:'#00e87c', FREEZE:'#ff2d2d', DOWNGRADE:'#f59e0b', TIMEBOX_ACTIVE:'#a855f7', SAFE:'#6366f1' }[mode] || '#888'

  return (
    <div
      className={`barrier-card ${active ? 'barrier-active' : ''}`}
      style={{ borderColor: active ? color : undefined, boxShadow: active ? `0 0 16px ${glow}` : undefined }}
    >
      {active && <div className="agent-pulse-ring" style={{ borderColor: color }} />}
      <div className="bc-left">
        <span className="bc-icon">🛡</span>
        <div className="bc-names">
          <span className="bc-name" style={{ color: active ? color : undefined }}>BARRIER</span>
          <span className="bc-role">Sole ALLOW/DENY Authority</span>
        </div>
      </div>
      <div className="bc-right">
        <div className="ac-status" style={{ color: color }}>● LISTENING</div>
        <div className="bc-mode">Mode: <span style={{ color: modeColor, fontWeight: 700 }}>{mode}</span></div>
      </div>
    </div>
  )
}
