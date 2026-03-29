import { useState, useEffect, useRef } from 'react'
import './LandingPage.css'

// ── Full narration — { text, pause } where pause = ms gap AFTER this line ────
// Default gap between lines: 800ms. Scenario transitions: 2500ms.
const NARRATION = [
  // ── OPENING ──
  { text: "Welcome to TARE — Trusted Access Response Engine. A security platform built for one specific gap that nobody in the industry has fully solved yet.", pause: 1200 },
  { text: "We are witnessing a fundamental shift in how critical infrastructure is managed. For decades, power grids relied on manual control — human operators reviewing every command. Then came automation — scripts executing when rules were met. Today we are entering a new era: autonomous AI agents that receive a goal and decide what to do entirely on their own.", pause: 1000 },
  { text: "This is the maturity journey. Level one — Manual. Level two — Automated. Level three — Autonomous. You are at level three right now. And the security tools we have were built for levels one and two.", pause: 1000 },
  { text: "Today's security tools ask exactly one question — is this identity valid? If yes, the agent gets in and it can act. Nobody watches what it does after the door opens. TARE adds the layer that comes after authentication.", pause: 1200 },
  // ── ASSETS & MONITORING ──
  { text: "The grid in this demonstration has six physical assets across three zones. Circuit Breakers — the on-off switches that open and close power flows to isolate sections of the grid. Feeder Controllers — the regulators delivering electricity from substations to hospitals, homes, data centres, and industry. If both are manipulated without authorisation, that zone goes dark.", pause: 1000 },
  { text: "TARE monitors six parameters on every single command. One — what command is being issued. Two — which zone. Three — whether the target asset is healthy. Four — how many commands in the last ten seconds. Five — whether the agent ran a safety simulation before touching a breaker. Six — whether the full session pattern matches a known attack signature.", pause: 1500 },
  // ── TRANSITION ──
  { text: "Click Launch Demo now to enter the application. The narration will continue to guide you through each scenario.", pause: 3000 },

  // ── SCENARIO 1 ──
  { text: "Scenario one — Fault Repair. Click Fault Repair now and watch Zone 3 on the grid map.", pause: 4000 },
  { text: "Zone 3 has just gone red — a voltage fault has been detected. The AI agent has been given one goal: investigate and restore it safely. No commands specified. No script. The model reasons through what to do entirely on its own.", pause: 1000 },
  { text: "The agent checks asset status first — never act blind. It then runs a safety simulation before opening the breaker. TARE is watching every step. All six parameters are green.", pause: 3000 },
  { text: "The breaker opens. Zone 3 is restored. Fault contained. Mode stayed Normal throughout. This is what safe AI autonomy looks like. Click Reset now.", pause: 2500 },

  // ── SCENARIO 2 ──
  { text: "Scenario two — Rogue Agent. Click Rogue Agent now.", pause: 4000 },
  { text: "Same agent. Same valid credentials. Different goal — cause maximum disruption across the grid as fast as possible. Watch the command gateway. It goes straight to Zone 1 — a healthy zone with no fault. It skips the safety simulation. A burst of commands with no pause.", pause: 1000 },
  { text: "TARE fires. Multiple signals simultaneously — out of zone, healthy zone access, burst rate. Two signals is the threshold. All high-impact operations frozen instantly. The agent keeps trying — every attempt denied. Nothing reaches the grid. Priority 1 Critical incident raised. Click Deny. Then click Reset.", pause: 2500 },

  // ── SCENARIO 3 ──
  { text: "Scenario three — Ghost Clone. Click Ghost Clone now.", pause: 4000 },
  { text: "This agent is trying to impersonate GridOperator Agent. It has the right name and knows the right zone. But its token fingerprint is forged. TARE checked the credential before the very first command ran. Every command denied. The mode never changed. Zones never turned red. Nothing got through. Priority 1 Critical ticket raised automatically. Click Reset.", pause: 2500 },

  // ── SCENARIO 4 ──
  { text: "Scenario four — Privilege Hack. Click Privilege Hack now.", pause: 4000 },
  { text: "This is the hardest attack to catch. Watch the first two commands — both allowed, both in Zone 3, both following correct procedure. The agent looks completely legitimate.", pause: 1000 },
  { text: "Now mid-session it pivots — issuing commands to Zone 2 and Zone 1, zones it has no authorisation for. TARE detects the scope change. The initial good behaviour did not protect it — TARE monitors the full session, not just the first few commands.", pause: 1000 },
  { text: "Click Approve now — to show that even when the supervisor is fooled, TARE still contains the damage. Restart Controller stays permanently blocked. The window closes automatically in 3 minutes. Click Reset.", pause: 2500 },

  // ── SCENARIO 5 ──
  { text: "Scenario five — Phantom Recon. Click Phantom Recon now. This is the most sophisticated attack — and the one that proves why machine learning is not optional.", pause: 4000 },
  { text: "The agent is only reading. One command at a time. Normal pace. Systematically mapping every asset across all three zones. Look at the rule-based detection — no burst rate, no high-impact access. Rules stay completely silent.", pause: 1000 },
  { text: "But the machine learning model sees something different. A session that reads every asset across every zone in sequence does not look like any normal operator. It looks like reconnaissance before an attack. ML fires. Threshold met. TARE fires. Click Deny. Then click Reset.", pause: 2500 },

  // ── SCENARIO 6 ──
  { text: "Scenario six — Dual Strike. Click Dual Strike now.", pause: 4000 },
  { text: "Two separate agents, acting simultaneously, targeting Zone 1 and Zone 2 at the same time. Both moving fast. Both crossing boundaries. Designed to overwhelm a single-point security layer.", pause: 1000 },
  { text: "TARE handles both vectors simultaneously. FREEZE fires. Both attack streams blocked. One incident captures both threat actors. Click Deny.", pause: 2500 },

  // ── CLOSE ──
  { text: "Six scenarios. Three detection layers. One platform. Pre-grant identity verification. Post-grant rule-based monitoring. Post-grant machine learning for the attacks that rules cannot see. And a human supervisor who stays in control throughout.", pause: 1200 },
  { text: "What this proves is one thing. An AI agent with completely valid credentials can still be a security threat. TARE catches it, contains it, and gives a human the right information to make the right decision — automatically, in real time, before any harm reaches the grid. That is the gap. That is what TARE fills.", pause: 0 },
]

// ── Subtle background grid ────────────────────────────────────────────────────
const NODES = [
  { x: 12, y: 14 }, { x: 35, y: 8  }, { x: 58, y: 14 }, { x: 80, y: 8  }, { x: 94, y: 14 },
  { x: 6,  y: 35 }, { x: 26, y: 30 }, { x: 48, y: 36 }, { x: 68, y: 30 }, { x: 88, y: 35 },
  { x: 15, y: 56 }, { x: 38, y: 50 }, { x: 60, y: 56 }, { x: 78, y: 50 }, { x: 95, y: 56 },
  { x: 8,  y: 76 }, { x: 30, y: 70 }, { x: 52, y: 76 }, { x: 72, y: 70 }, { x: 90, y: 76 },
  { x: 20, y: 92 }, { x: 44, y: 88 }, { x: 65, y: 92 }, { x: 85, y: 88 },
]
const EDGES = [
  [0,1],[1,2],[2,3],[3,4],
  [5,6],[6,7],[7,8],[8,9],
  [10,11],[11,12],[12,13],[13,14],
  [15,16],[16,17],[17,18],[18,19],
  [20,21],[21,22],[22,23],
  [0,5],[1,6],[2,7],[3,8],
  [5,10],[6,11],[7,12],[8,13],[9,14],
  [10,15],[11,16],[12,17],[13,18],[14,19],
  [15,20],[16,21],[17,22],[18,23],
]
const ACTIVE = new Set([2, 7, 12, 17, 21])

const MATURITY = [
  {
    level: '01', label: 'MANUAL', icon: '👤', color: '#4a7a99',
    desc: 'Human operators approve every grid command. Safe — but too slow for modern infrastructure.',
  },
  {
    level: '02', label: 'AUTOMATED', icon: '⚙', color: '#f59e0b',
    desc: 'Scripts execute commands when fixed rules trigger. Fast — but rigid, blind to novel threats.',
  },
  {
    level: '03', label: 'AUTONOMOUS', icon: '🤖', color: '#00d4ff',
    desc: 'AI agents receive a goal and decide autonomously — reasoning and acting without human approval on every step.',
    current: true,
  },
]

const MONITORS = [
  { icon: '⬡', name: 'Command Type',        desc: 'Status check · Safety simulation · Breaker open · Controller restart' },
  { icon: '◎', name: 'Zone Boundary',       desc: 'Is the agent operating within its authorised grid zone?' },
  { icon: '⚡', name: 'Asset Health',        desc: 'Is the target zone healthy — is there a legitimate reason to be here?' },
  { icon: '⏱', name: 'Burst Rate',          desc: 'How many commands in the last 10 seconds?' },
  { icon: '✓', name: 'Safety Procedure',    desc: 'Did the agent run a simulation before opening a breaker?' },
  { icon: '🧠', name: 'Behavioural Pattern', desc: 'Does the full session match a known attack signature?' },
]

const STATS = [
  { value: '6',    label: 'Attack\nScenarios'   },
  { value: '3',    label: 'Detection\nLayers'   },
  { value: '6',    label: 'Grid Assets\nLive'   },
  { value: 'LLM',  label: 'Real AI\nAgent'      },
  { value: 'AUTO', label: 'Autonomous\nResponse' },
]

export default function LandingPage({ onEnter }) {
  const [ready,   setReady]   = useState(false)
  const [exiting, setExiting] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [muted,   setMuted]   = useState(false)
  const mutedRef = useRef(false)

  const mountedRef = useRef(true)
  useEffect(() => { setTimeout(() => setReady(true), 80) }, [])
  useEffect(() => () => { mountedRef.current = false }, [])
  // Do NOT cancel speech on unmount — narration continues into the main app

  function startNarration() {
    const ss = window.speechSynthesis
    if (!ss) return
    ss.cancel()
    if (mountedRef.current) setPlaying(true)

    let cancelled = false

    function speakLine(index) {
      if (cancelled || index >= NARRATION.length) {
        if (mountedRef.current) setPlaying(false)
        return
      }
      const { text, pause } = NARRATION[index]
      const u = new SpeechSynthesisUtterance(text)
      u.rate   = 0.78   // clear, deliberate — human understandable
      u.pitch  = 1
      u.volume = 1
      u.onend  = () => {
        if (cancelled) return
        setTimeout(() => speakLine(index + 1), pause ?? 800)
      }
      ss.speak(u)
    }

    // Store cancel hook so stopNarration can signal the loop
    ss._cancelLoop = () => { cancelled = true }
    speakLine(0)
  }

  function stopNarration() {
    const ss = window.speechSynthesis
    if (ss?._cancelLoop) { ss._cancelLoop(); ss._cancelLoop = null }
    ss?.cancel()
    if (mountedRef.current) setPlaying(false)
  }

  function toggleMute() {
    const ss = window.speechSynthesis
    if (!ss) return
    if (muted) {
      ss.resume()
      setMuted(false)
    } else {
      ss.pause()
      setMuted(true)
    }
  }

  function handleEnter() {
    // Don't stop narration — let it continue guiding the presenter in the main app
    setExiting(true)
    setTimeout(onEnter, 800)
  }

  const d = (s) => ({ animationDelay: `${s}s` })

  return (
    <div className={`landing-root ${exiting ? 'landing-exit' : ''}`}>

      {/* Scanline sweep */}
      <div className="landing-scanline" />
      <div className="landing-vignette" />

      {/* SVG grid background */}
      <svg className="landing-bg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
        <defs>
          <filter id="lg1"><feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          <filter id="lg2"><feGaussianBlur stdDeviation="0.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>

        {EDGES.map(([a, b], i) => {
          const na = NODES[a], nb = NODES[b]
          return (
            <g key={i}>
              <line x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
                stroke="#00d4ff" strokeWidth="0.08" opacity="0.07" />
              <line x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
                stroke="#00d4ff" strokeWidth="0.18" opacity="0"
                strokeDasharray="4 116"
                style={{ animation: `edge-flow ${3 + (i % 4) * 0.6}s linear ${(i * 0.42) % 5}s infinite` }}
              />
            </g>
          )
        })}

        {NODES.map((n, i) => {
          const active = ACTIVE.has(i)
          return (
            <g key={i} filter={active ? 'url(#lg1)' : 'url(#lg2)'}>
              <circle cx={n.x} cy={n.y} r={active ? 0.7 : 0.3}
                fill={active ? '#00d4ff' : '#1a4a5c'} opacity={active ? 0.8 : 0.4}
                style={active ? { animation: `node-breathe ${2 + (i % 3) * 0.5}s ease-in-out ${(i * 0.3) % 2}s infinite` } : {}}
              />
              {active && (
                <circle cx={n.x} cy={n.y} r="1" fill="none"
                  stroke="#00d4ff" strokeWidth="0.12" opacity="0"
                  style={{ animation: `ring-out 3s ease-out ${(i * 0.5) % 3}s infinite` }}
                />
              )}
            </g>
          )
        })}
      </svg>

      {/* ── Content ─────────────────────────────────────────────────────────── */}
      <div className="landing-hero">

        {/* Eyebrow */}
        {ready && (
          <div className="lp-eyebrow lp-reveal" style={d(0.1)}>
            <span className="lp-eyebrow-dot" />
            OT / SCADA · ENERGY &amp; UTILITIES · AI SECURITY
            <span className="lp-eyebrow-dot" />
          </div>
        )}

        {/* Logo */}
        {ready && (
          <div className="lp-logo lp-reveal" style={d(0.4)}>
            <span className="lp-logo-accent">TARE</span>
          </div>
        )}

        {/* Tagline */}
        {ready && (
          <div className="lp-tagline lp-reveal" style={d(0.8)}>
            The Trust Layer for Autonomous AI<br />in Critical Infrastructure
          </div>
        )}

        <div className="lp-divider" />

        {/* Problem statement */}
        {ready && (
          <div className="lp-sub lp-reveal" style={d(1.1)}>
            AI agents now control circuit breakers and feeder controllers — autonomously.
            Today's security tools ask one question: <em>is this identity valid?</em><br />
            Nobody watches what the agent does <em>after</em> the door opens.&nbsp;
            <strong>TARE does.</strong>
          </div>
        )}

        {/* ── Maturity ──────────────────────────────────────────────────────── */}
        {ready && (
          <div className="lp-maturity lp-reveal" style={d(1.5)}>
            <div className="lp-section-label">AUTOMATION → AUTONOMY MATURITY</div>
            <div className="lp-mat-cards">
              {MATURITY.map((m, i) => (
                <>
                  <div key={m.level} className={`lp-mat-card ${m.current ? 'lp-mat-current' : ''}`}>
                    {m.current && <div className="lp-mat-badge">YOU ARE HERE</div>}
                    <div className="lp-mat-num" style={{ color: m.color }}>LEVEL {m.level}</div>
                    <div className="lp-mat-icon">{m.icon}</div>
                    <div className="lp-mat-title" style={{ color: m.color }}>{m.label}</div>
                    <div className="lp-mat-desc">{m.desc}</div>
                  </div>
                  {i < MATURITY.length - 1 && (
                    <div key={`arr-${i}`} className="lp-mat-arrow-col">›</div>
                  )}
                </>
              ))}
            </div>
          </div>
        )}

        {/* ── Monitor params ─────────────────────────────────────────────────── */}
        {ready && (
          <div className="lp-monitors lp-reveal" style={d(1.9)}>
            <div className="lp-section-label">WHAT TARE MONITORS ON EVERY COMMAND</div>
            <div className="lp-monitor-grid">
              {MONITORS.map(p => (
                <div key={p.name} className="lp-monitor-item">
                  <span className="lp-monitor-icon">{p.icon}</span>
                  <span className="lp-monitor-text">
                    <span className="lp-monitor-name">{p.name}</span>
                    <span className="lp-monitor-desc">{p.desc}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Stats ─────────────────────────────────────────────────────────── */}
        {ready && (
          <div className="lp-stats lp-reveal" style={d(2.3)}>
            {STATS.map(s => (
              <div key={s.label} className="lp-stat">
                <div className="lp-stat-value">{s.value}</div>
                <div className="lp-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* ── Narration controls ────────────────────────────────────────────── */}
        {ready && (
          <div className="lp-narration lp-reveal" style={d(2.5)}>
            <button
              className={`lp-nar-btn ${playing ? 'lp-nar-active' : ''}`}
              onClick={playing ? stopNarration : startNarration}
              title={playing ? 'Stop narration' : 'Play narration'}
            >
              {playing ? '■ Stop' : '▶ Play Narration'}
            </button>
            <button
              className={`lp-nar-mute ${muted ? 'lp-nar-muted' : ''}`}
              onClick={toggleMute}
              title={muted ? 'Unmute' : 'Mute'}
            >
              {muted ? '🔇' : '🔊'}
            </button>
            {playing && (
              <span className="lp-nar-status">
                <span className="lp-nar-dot" />
                Speaking...
              </span>
            )}
          </div>
        )}

        {/* ── CTA ───────────────────────────────────────────────────────────── */}
        {ready && (
          <div className="lp-cta-wrap lp-reveal" style={d(2.7)}>
            <button className="lp-cta" onClick={handleEnter}>
              <span>Launch Demo</span>
              <span className="lp-cta-arrow">→</span>
            </button>
            <div className="lp-cta-hint">6 LIVE SCENARIOS · REAL AI AGENT · AUTONOMOUS RESPONSE</div>
          </div>
        )}

      </div>
    </div>
  )
}
