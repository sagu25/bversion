import { useEffect, useRef, useState } from 'react'

function fmtTs(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('en-GB', { hour12:false })
}

function scrollToBottom(ref) {
  setTimeout(() => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }), 60)
}

const SUGGESTIONS = [
  'How many agents went rogue?',
  'Any scope creep this session?',
  'Identity mismatches?',
  'Show session summary',
  'Any freeze events?',
  'ML anomalies detected?',
  'Active incidents?',
]

export default function ChatAssistant({ messages, showApprove, onApprove, onDeny }) {
  const bottomRef  = useRef(null)
  const inputRef   = useRef(null)
  const [input,    setInput]    = useState('')
  const [chatLog,  setChatLog]  = useState([])
  const [loading,  setLoading]  = useState(false)

  useEffect(() => { scrollToBottom(bottomRef) }, [messages, chatLog, loading])

  const ask = async (question) => {
    const q = question.trim()
    if (!q) return
    setInput('')
    setChatLog(prev => [...prev, { role:'user', text:q, ts: new Date().toISOString() }])
    setLoading(true)
    try {
      const res  = await fetch('/chat/query', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ question: q })
      })
      const data = await res.json()
      setChatLog(prev => [...prev, { role:'tare', text: data.answer, ts: new Date().toISOString() }])
    } catch {
      setChatLog(prev => [...prev, { role:'tare', text:'Unable to reach TARE backend.', ts: new Date().toISOString() }])
    }
    setLoading(false)
  }

  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(input) } }

  const allMsgs = [
    ...messages.map(m => ({ ...m, _src:'tare' })),
    ...chatLog.map(m => ({ ...m, _src:'user' })),
  ].sort((a, b) => new Date(a.ts) - new Date(b.ts))

  return (
    <div className="panel chat-panel">
      <div className="panel-title"><span className="panel-icon">💬</span> Ask TARE</div>

      <div className="chat-body">
        {allMsgs.length === 0 && (
          <div className="chat-empty">TARE will narrate decisions here. Ask a question below.</div>
        )}
        {allMsgs.map((m, i) => (
          <div key={i} className={`chat-msg msg-${m.role}`}>
            <div className="msg-meta">
              <span className={`msg-role ${m._src === 'user' && m.role === 'tare' ? 'msg-role-answer' : ''}`}>
                {m.role === 'tare' ? (m._src === 'user' ? '🤖 TARE Answer' : 'TARE Engine') : m.role === 'user' ? 'You' : 'System'}
              </span>
              <span className="msg-ts">{fmtTs(m.ts)}</span>
            </div>
            <div className="msg-text">{m.text}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-msg msg-tare">
            <div className="msg-meta"><span className="msg-role">TARE Engine</span></div>
            <div className="msg-text chat-typing">Analysing session data<span>...</span></div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {chatLog.length === 0 && !loading && (
        <div className="chat-suggestions">
          {SUGGESTIONS.map(s => (
            <button key={s} className="chat-suggestion-btn" onClick={() => ask(s)}>{s}</button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="chat-input-row">
        <input
          ref={inputRef}
          className="chat-input"
          placeholder="Ask about session activity…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKey}
          disabled={loading}
        />
        <button className="chat-send-btn" onClick={() => ask(input)} disabled={loading || !input.trim()}>
          ➤
        </button>
      </div>

      {showApprove && (
        <div className="approve-bar">
          <div className="approve-label">Supervisor decision required</div>
          <div className="approve-actions">
            <button className="approve-btn" onClick={onApprove}>✓ Approve 3-min Time-Box</button>
            <button className="deny-btn" onClick={onDeny}>✕ Deny / Escalate</button>
          </div>
        </div>
      )}
    </div>
  )
}
