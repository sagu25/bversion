import { useRef, useEffect } from 'react'

const LEVEL_CLS = {
  info:    'feed-info',
  danger:  'feed-danger',
  warning: 'feed-warning',
  ok:      'feed-ok',
}

function fmtTs(ts) {
  if (!ts) return ''
  return ts.slice(11, 19)
}

export default function ActivityFeed({ feedItems }) {
  const listRef = useRef(null)

  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTop = 0
  }, [feedItems])

  return (
    <div className="panel feed-panel">
      <div className="panel-title"><span className="panel-icon">📋</span> Activity Feed</div>
      <div className="feed-body" ref={listRef}>
        {feedItems.map(item => (
          <div key={item.id} className={`feed-row ${LEVEL_CLS[item.level] || ''}`}>
            <span className="feed-ts">{fmtTs(item.ts)}</span>
            <span className="feed-src">{item.source}</span>
            <span className="feed-msg">{item.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
