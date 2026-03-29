import { useState, useEffect } from 'react'

export default function Header({ wsConnected, darkMode, onToggleTheme }) {
  const [now,      setNow]      = useState(new Date())
  const [narOn,    setNarOn]    = useState(false)   // speech active or paused
  const [narMuted, setNarMuted] = useState(false)

  useEffect(() => { const t = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(t) }, [])

  // Poll speechSynthesis to know if narration is active
  useEffect(() => {
    const t = setInterval(() => {
      const ss = window.speechSynthesis
      if (!ss) return
      setNarOn(ss.speaking || ss.paused)
      setNarMuted(ss.paused)
    }, 400)
    return () => clearInterval(t)
  }, [])

  function toggleNarMute() {
    const ss = window.speechSynthesis
    if (!ss) return
    if (ss.paused) { ss.resume(); setNarMuted(false) }
    else if (ss.speaking) { ss.pause(); setNarMuted(true) }
  }

  function stopNar() {
    window.speechSynthesis?.cancel()
    setNarOn(false)
    setNarMuted(false)
  }

  const timeStr = now.toLocaleTimeString('en-GB', { hour12:false })
  const dateStr = now.toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' })

  return (
    <header className="tare-header">
      {/* Brand */}
      <div className="hdr-brand">
        <div className="hdr-logo">TARE <span style={{ color: 'var(--accent-blue)', fontWeight: 700, fontSize: '0.8em', letterSpacing: '0.12em', verticalAlign: 'middle' }}>— AI OBSERVABILITY</span></div>
        <div className="hdr-sub">Trusted Access Response Engine · E&amp;U Security Platform</div>
      </div>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Status + clock */}
      <div className="hdr-right">
        {narOn && (
          <>
            <button className="hdr-nar-btn" onClick={toggleNarMute}
              title={narMuted ? 'Resume narration' : 'Pause narration'}>
              {narMuted ? '▶' : '⏸'}
            </button>
            <button className="hdr-nar-btn hdr-nar-stop" onClick={stopNar} title="Stop narration">
              ■
            </button>
            <span className="hdr-nar-label">{narMuted ? 'PAUSED' : '● NARRATING'}</span>
          </>
        )}
        <button className="theme-toggle" onClick={onToggleTheme} title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}>
          {darkMode ? '☀' : '☾'}
        </button>
        <span className={`ws-dot ${wsConnected ? 'on' : 'off'}`} />
        <span className="ws-label">{wsConnected ? 'LIVE' : 'OFFLINE'}</span>
        <span className="hdr-clock">{dateStr} &nbsp; {timeStr} UTC</span>
      </div>
    </header>
  )
}
