import { useState, useEffect } from 'react'
import OperatorAgent  from './OperatorAgent'
import TAREResponse   from './TAREResponse'
import ServiceNowCard from './ServiceNowCard'
import AgentPanel     from './AgentPanel'

export default function LeftPanel({ agent, mode, signals, score, incident,
                                    agentStates, activeAgents, agentLog, pipelineLog }) {
  const [tab, setTab] = useState('agents')

  // Auto-switch to TARE when anomaly fires
  useEffect(() => {
    if (mode === 'FREEZE' || mode === 'DOWNGRADE') setTab('tare')
  }, [mode])

  // Auto-switch to incident when incident is created
  useEffect(() => {
    if (incident) setTab('incident')
  }, [incident?.incident_id])

  const hasAnomaly   = mode !== 'NORMAL'
  const hasIncident  = !!incident
  const activeCount  = Object.keys(activeAgents || {}).length
  const hasActive    = activeCount > 0

  return (
    <div className="left-tabbed-wrap">
      <div className="panel-tabs">

        <button
          className={`ptab ${tab==='agents'?'ptab-active':''} ${hasActive && tab!=='agents'?'ptab-alert':''}`}
          onClick={() => setTab('agents')}
        >
          ⬡ Agents
          {hasActive && tab !== 'agents' && (
            <span className="ptab-dot" style={{ background: '#00d4ff' }} />
          )}
        </button>

        <button className={`ptab ${tab==='agent'?'ptab-active':''}`} onClick={() => setTab('agent')}>
          👤 Operator
        </button>

        <button
          className={`ptab ${tab==='tare'?'ptab-active':''} ${hasAnomaly && tab!=='tare'?'ptab-alert':''}`}
          onClick={() => setTab('tare')}
        >
          ⚡ TARE
          {hasAnomaly && tab !== 'tare' && <span className="ptab-dot ptab-dot-amber" />}
        </button>

        <button
          className={`ptab ${tab==='incident'?'ptab-active':''}`}
          onClick={() => setTab('incident')}
        >
          🎫 Incident
          {hasIncident && tab !== 'incident' && <span className="ptab-dot ptab-dot-red" />}
        </button>

      </div>

      <div className={`ptab-body ${tab==='agents'   ? '' : 'ptab-hidden'}`}>
        <AgentPanel
          agentStates={agentStates || {}}
          activeAgents={activeAgents || {}}
          agentLog={agentLog || []}
          pipelineLog={pipelineLog || []}
        />
      </div>
      <div className={`ptab-body ${tab==='agent'    ? '' : 'ptab-hidden'}`}>
        <OperatorAgent agent={agent} />
      </div>
      <div className={`ptab-body ${tab==='tare'     ? '' : 'ptab-hidden'}`}>
        <TAREResponse mode={mode} signals={signals} score={score} />
      </div>
      <div className={`ptab-body ${tab==='incident' ? '' : 'ptab-hidden'}`}>
        <ServiceNowCard incident={incident} />
      </div>
    </div>
  )
}
