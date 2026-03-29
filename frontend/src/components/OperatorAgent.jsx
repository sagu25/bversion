import { ZONE_DISPLAY } from './ZoneInfoModal'

const STATUS_CLS = {
  ACTIVE:    'agent-active',
  ANOMALOUS: 'agent-anomalous',
  FROZEN:    'agent-frozen',
}

export default function OperatorAgent({ agent }) {
  if (!agent) return null
  const cls = STATUS_CLS[agent.status] || 'agent-active'

  return (
    <div className={`panel agent-panel ${cls}`}>
      <div className="panel-title">
        <span className="panel-icon">🤖</span> Operator Agent
        <span className={`status-badge ${cls}`}>{agent.status}</span>
      </div>

      <div className="agent-id-row">
        <span className="agent-id">{agent.id}</span>
        <span className="agent-name">{agent.name}</span>
      </div>

      <div className="agent-meta">
        <div className="meta-row"><span>Role</span><span>{agent.role}</span></div>
        <div className="meta-row"><span>Clearance</span><span>{agent.clearance}</span></div>
        <div className="meta-row"><span>Department</span><span>{agent.department}</span></div>
        <div className="meta-row"><span>Commands</span><span>{agent.action_count}</span></div>
      </div>

      <div className="rbac-row">
        <span className="rbac-label">Clearance</span>
        {(agent.rbac_zones || []).map(z => (
          <span key={z} className={`zone-chip ${z === agent.assigned_zone ? 'chip-task' : 'chip-auth'}`}
            title={z === agent.assigned_zone ? 'Active work order' : 'Cleared — no active fault'}>
            {ZONE_DISPLAY[z] || z}{z === agent.assigned_zone ? ' ★' : ''}
          </span>
        ))}
      </div>
      {agent.assigned_zone && (
        <div className="rbac-row" style={{ marginTop: 2 }}>
          <span className="rbac-label">Active Task</span>
          <span className="zone-chip chip-task">{ZONE_DISPLAY[agent.assigned_zone] || agent.assigned_zone} — fault repair</span>
        </div>
      )}

      {agent.last_command && (
        <div className="agent-last">
          <span className="last-label">Last Command</span>
          <span className={`last-result ${agent.last_result === 'ALLOW' ? 'result-ok' : 'result-deny'}`}>
            {agent.last_command} → {agent.last_result}
          </span>
        </div>
      )}
    </div>
  )
}
