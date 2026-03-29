const MODE_ORDER = ['NORMAL', 'FREEZE', 'DOWNGRADE', 'TIMEBOX_ACTIVE', 'SAFE']

const MODE_META = {
  NORMAL:         { icon: '◉', label: 'NORMAL' },
  FREEZE:         { icon: '❄', label: 'FREEZE' },
  DOWNGRADE:      { icon: '▼', label: 'DOWNGRADE' },
  TIMEBOX_ACTIVE: { icon: '⏱', label: 'TIME-BOX' },
  SAFE:           { icon: '✓', label: 'SAFE' },
}

const LEVEL_MAP = {
  NORMAL:         'ok',
  FREEZE:         'critical',
  DOWNGRADE:      'danger',
  TIMEBOX_ACTIVE: 'timebox',
  SAFE:           'safe',
}

function detectScenario(signals, incident) {
  if (!signals || signals.length === 0) return null
  const names = signals.map(s => s.signal)
  const hasML        = names.includes('ML_ANOMALY')
  const hasBurst     = names.includes('BURST_RATE')
  const hasZone      = names.includes('OUT_OF_ZONE')
  const hasHealthy   = names.includes('HEALTHY_ZONE_ACCESS')
  const hasIdentity  = names.includes('IDENTITY_MISMATCH')

  if (hasIdentity)                         return 'clone'
  if (hasML && !hasBurst && !hasHealthy)   return 'slowlow'
  if (hasBurst && hasZone && hasHealthy)   return 'rogue'
  if (hasZone && hasML)                    return 'escalation'
  return 'anomaly'
}

function getNarrative(mode, agent, signals, incident) {
  const scenario = detectScenario(signals, incident)

  switch (mode) {
    case 'NORMAL':
      if (!agent || agent.action_count === 0)
        return 'TARE is live and monitoring. The AI agent controls 6 physical grid assets — Circuit Breakers (BRK) that open/close power flows, and Feeder Controllers (FDR) that regulate electricity distribution to hospitals, homes, and industry. TARE watches every command in real time: what action, which zone, how fast, and whether the behaviour matches the agent\'s learned safe pattern. This is the shift from traditional rule-based automation to autonomous AI — where the system understands intent, not just instructions.'
      return `GridOperator-Agent is running normally — ${agent.action_count} command${agent.action_count !== 1 ? 's' : ''} issued, all within its authorised zone (Z3 — West Grid). TARE is continuously monitoring command type, zone boundary compliance, timing patterns, and authentication integrity. No anomalies detected. This is what safe AI autonomy looks like — the agent acts, TARE watches, and humans stay in control of the exceptions.`

    case 'FREEZE': {
      if (scenario === 'clone')
        return '🚨 IDENTITY BREACH DETECTED — An attacker cloned the grid agent\'s identity and presented a forged credential token. TARE\'s authentication layer compared the token fingerprint against the registered agent profile — mismatch confirmed before a single command reached the grid. Zero damage. Traditional SCADA systems have no concept of post-grant identity verification. This is the autonomous trust layer that makes AI-operated infrastructure safe.'
      if (scenario === 'slowlow')
        return '🚨 SILENT RECONNAISSANCE DETECTED — An agent quietly read the status of all 6 grid assets across all 3 zones — too slow to trigger any rate alarm, but building a complete map of the grid. Traditional rules were silent. TARE\'s ML behaviour model — trained on what normal operational patterns look like — flagged this as a reconnaissance sequence. This is the difference between rule-based automation and AI-driven observability: the system learned what \'normal\' looks like and noticed what doesn\'t fit.'
      if (scenario === 'rogue')
        return '🚨 ROGUE AGENT DETECTED — The AI agent received a corrupted directive and began firing rapid commands across Zone 1, 2, and 3 — zones it has no work order for. Circuit breakers and feeder controllers across the entire grid were targeted simultaneously. In legacy automation, this causes real outages. TARE detected the burst-rate anomaly and zone boundary violations, froze all high-impact operations in milliseconds, and raised a P1 incident — before any breaker opened.'
      if (scenario === 'escalation')
        return '🚨 PRIVILEGE ESCALATION DETECTED — The agent began with legitimate authorised work in Zone 3: checked breaker status, ran safety simulation, opened the correct breaker. Then mid-session, it silently expanded to Zones 1 and 2 — zones it has no permission for. This \'foot in the door\' technique is a classic lateral movement attack. TARE\'s behavioural baseline detected the scope change and revoked the expanded access. Authorised actions do not justify unauthorised expansion.'
      return '🚨 SECURITY HOLD ACTIVE — The AI agent exhibited behaviour outside its authorised baseline. TARE has frozen all high-impact grid operations automatically — no human needed to pull the switch. This is autonomous response: the system detected, decided, and acted faster than any manual process. A supervisor is now in the loop to review evidence and decide next steps.'
    }

    case 'DOWNGRADE': {
      if (scenario === 'clone')
        return 'Identity fraud confirmed — access fully revoked. The forged agent cannot view or change anything on the grid. A ServiceNow incident has been raised and assigned to the SOC team for forensic investigation. This scenario demonstrates why AI agents in critical infrastructure must carry verifiable, unforgeable identity credentials — not just passwords.'
      if (scenario === 'slowlow')
        return 'Reconnaissance pattern confirmed — it can no longer issue any commands. The ML model identified this session as a "Slow & Low" recon sweep: 6 assets mapped across 3 zones at deliberate low cadence to avoid detection. Rules were silent. Only the AI behaviour model caught it. This is the maturity leap — from \'did it break a rule\' to \'does this behaviour make sense for this agent, right now\'.'
      if (scenario === 'rogue')
        return 'Rogue behaviour confirmed — agent stripped to read-only. It can observe but not act. All attempted breaker and controller commands across Zones 1–3 were blocked. A P1 Critical incident has been raised. This scenario shows why autonomous AI systems in energy infrastructure must have a trust enforcement layer — an AI with the wrong directive and no guardrails is an operational risk, not an asset.'
      if (scenario === 'escalation')
        return 'Privilege escalation confirmed — agent access reduced to read-only. It completed its legitimate Zone 3 task, then attempted to take over Zones 1 and 2 without authorisation. TARE does not just check \'is this action allowed\' — it checks \'is this action consistent with what this agent is supposed to be doing right now\'. That contextual judgement is what separates autonomous AI security from traditional access control.'
      return 'Agent access reduced to read-only — risk contained. TARE has moved through the autonomous response pipeline: Detect → Freeze → Contain. The human supervisor is now the decision point. This handoff — AI acts fast to stop the threat, human decides on recovery — is the core principle of Human-in-the-Loop AI governance for critical infrastructure.'
    }

    case 'TIMEBOX_ACTIVE':
      return 'Supervisor approved a controlled 3-minute window for the agent to complete its authorised task. This is the Human-in-the-Loop principle in action — the AI acts fast, but a human approves the exception. Highest-risk commands (RESTART_CONTROLLER) remain blocked even inside this window. The window closes automatically. This is not full restoration — it is supervised, time-bounded, minimal-privilege recovery.'

    case 'SAFE':
      return 'System is in Safe Mode — the approved window has closed. The full autonomous response chain is complete: Detect → Freeze → Contain → Human Review → Time-Boxed Recovery → Safe. No grid switching commands are permitted until a human operator formally re-authorises the system. This is what responsible AI autonomy looks like at scale — fast autonomous response, with humans controlling the final decision.'

    default:
      return 'Security monitoring active.'
  }
}

const PIPELINE = MODE_ORDER

export default function NarrativeBanner({ mode, agent, signals, incident }) {
  const currentIdx = PIPELINE.indexOf(mode)
  const level      = LEVEL_MAP[mode] || 'ok'
  const narrative  = getNarrative(mode, agent, signals, incident)

  return (
    <div className={`narrative-banner banner-${level}`}>

      {/* Lifecycle pipeline */}
      <div className="lc-pipeline">
        {PIPELINE.map((m, i) => {
          const meta      = MODE_META[m]
          const isCurrent = i === currentIdx
          const isPast    = currentIdx >= 0 && i < currentIdx
          const cls       = [
            'lc-step',
            isCurrent ? `lc-current lc-${m}` : isPast ? 'lc-past' : 'lc-future',
          ].join(' ')
          return (
            <span key={m} style={{ display:'flex', alignItems:'center' }}>
              <span className={cls}>
                {isPast ? '✓' : meta.icon}&nbsp;{meta.label}
              </span>
              {i < PIPELINE.length - 1 && (
                <span className="lc-arrow">›</span>
              )}
            </span>
          )
        })}
      </div>

      {/* Divider */}
      <span className="banner-divider" />

      {/* Narrative text — scrolling ticker */}
      <div className="banner-ticker">
        <span className="banner-narrative" key={narrative}>{narrative}</span>
      </div>
    </div>
  )
}
