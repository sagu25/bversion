import { useEffect, useRef } from 'react'

function fmtTs(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('en-GB', { hour12:false })
}

export default function ChatAssistant({ messages, showApprove, onApprove, onDeny }) {
  const bottomRef = useRef(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior:'smooth' })
  }, [messages])

  return (
    <div className="panel chat-panel">
      <div className="panel-title"><span className="panel-icon">💬</span> TARE Assistant</div>

      <div className="chat-body">
        {messages.length === 0 && (
          <div className="chat-empty">TARE will narrate decisions here…</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg msg-${m.role}`}>
            <div className="msg-meta">
              <span className="msg-role">{m.role === 'tare' ? 'TARE Engine' : 'System'}</span>
              <span className="msg-ts">{fmtTs(m.ts)}</span>
            </div>
            <div className="msg-text">{m.text}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {showApprove && (
        <div className="approve-bar">
          <div className="approve-label">Supervisor decision required</div>
          <div className="approve-actions">
            <button className="approve-btn" onClick={onApprove}>
              ✓ Approve 3-min Time-Box
            </button>
            <button className="deny-btn" onClick={onDeny}>
              ✕ Deny / Escalate
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
