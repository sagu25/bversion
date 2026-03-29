import { useState, useEffect, useRef } from 'react'
import CommandGateway from './CommandGateway'
import ChatAssistant  from './ChatAssistant'
import ActivityFeed   from './ActivityFeed'

export default function BottomTabs({ gatewayLog, chatMsgs, feedItems, showApprove, onApprove, onDeny, onZoneClick, mode }) {
  const [tab, setTab]       = useState('gateway')
  const [unread, setUnread] = useState(0)
  const prevFeedLen = useRef(feedItems.length)
  const prevMsgLen  = useRef(chatMsgs.length)

  // Badge: new activity items when not on activity tab
  useEffect(() => {
    const diff = feedItems.length - prevFeedLen.current
    if (tab !== 'feed' && diff > 0) setUnread(n => n + diff)
    prevFeedLen.current = feedItems.length
  }, [feedItems.length])

  // Auto-switch to TARE Assistant when a new chat message arrives
  useEffect(() => {
    if (chatMsgs.length > prevMsgLen.current) setTab('chat')
    prevMsgLen.current = chatMsgs.length
  }, [chatMsgs.length])

  // Auto-switch to TARE Assistant on freeze/anomaly (mirrors left panel behaviour)
  useEffect(() => {
    if (mode === 'FREEZE' || mode === 'DOWNGRADE') setTab('chat')
  }, [mode])

  const switchTab = (t) => {
    setTab(t)
    if (t === 'feed') setUnread(0)
  }

  const hasApprove = showApprove && tab !== 'chat'

  return (
    <div className="bottom-tabs-wrap">
      {/* Horizontal tab bar */}
      <div className="panel-tabs bottom-panel-tabs">
        <button
          className={`ptab ${tab === 'gateway' ? 'ptab-active' : ''}`}
          onClick={() => switchTab('gateway')}
        >
          🛡 Command Gateway
        </button>
        <button
          className={`ptab ${tab === 'chat' ? 'ptab-active' : ''} ${hasApprove ? 'ptab-alert' : ''}`}
          onClick={() => switchTab('chat')}
        >
          💬 TARE Assistant
          {hasApprove && <span className="ptab-dot ptab-dot-amber" />}
        </button>
        <button
          className={`ptab ${tab === 'feed' ? 'ptab-active' : ''}`}
          onClick={() => switchTab('feed')}
        >
          📋 Activity
          {unread > 0 && tab !== 'feed' && (
            <span className="ptab-count">{unread > 9 ? '9+' : unread}</span>
          )}
        </button>
      </div>

      {/* Tab bodies */}
      <div className={`ptab-body bottom-ptab-body ${tab === 'gateway' ? '' : 'ptab-hidden'}`}>
        <CommandGateway log={gatewayLog} onZoneClick={onZoneClick} />
      </div>
      <div className={`ptab-body bottom-ptab-body ${tab === 'chat' ? '' : 'ptab-hidden'}`}>
        <ChatAssistant messages={chatMsgs} showApprove={showApprove} onApprove={onApprove} onDeny={onDeny} />
      </div>
      <div className={`ptab-body bottom-ptab-body ${tab === 'feed' ? '' : 'ptab-hidden'}`}>
        <ActivityFeed feedItems={feedItems} />
      </div>
    </div>
  )
}
