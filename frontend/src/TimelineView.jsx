import { useEffect, useRef, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function parseYear(startDate) {
  if (!startDate) return ''
  if (startDate.startsWith('-')) {
    const year = startDate.slice(1).split('-')[0].replace(/^0+/, '') || '0'
    return 'BC ' + year
  }
  const year = startDate.split('-')[0].replace(/^0+/, '') || '1'
  return 'AD ' + year
}

function TimelineView({ onSelectNode, selectedNode }) {
  const [events, setEvents] = useState([])
  const [openGroup, setOpenGroup] = useState(null)
  const containerRef = useRef(null)

  useEffect(() => {
    fetch(`${API_URL}/events`)
      .then(r => r.json())
      .then(data => setEvents(data))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (openGroup === null) return
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpenGroup(null)
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [openGroup])

  const groupMap = new Map()
  for (const ev of events) {
    const key = ev.startDate ?? ''
    if (!groupMap.has(key)) groupMap.set(key, [])
    groupMap.get(key).push(ev)
  }

  const groups = Array.from(groupMap.entries())
    .map(([startDate, members]) => {
      const sortKey = members[0].sortKey ?? startDate
      const rep = members.find(e => e.nameKo) || members[0]
      return { startDate, members, sortKey, rep }
    })
    .sort((a, b) => {
      if (a.sortKey < b.sortKey) return -1
      if (a.sortKey > b.sortKey) return 1
      return 0
    })

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', overflowY: 'auto', background: '#fafafa', position: 'relative' }}
    >
      {groups.map(({ startDate, members, rep }) => {
        const isSelected = selectedNode && members.some(e => e.id === selectedNode)
        const yearLabel = parseYear(startDate)
        const isSingle = members.length === 1
        const groupKey = startDate

        return (
          <div
            key={groupKey}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              padding: '4px 8px',
              minHeight: '28px',
              backgroundColor: isSelected ? '#fff3cd' : 'transparent',
              cursor: isSingle ? 'pointer' : 'default',
              position: 'relative',
            }}
            onClick={isSingle ? () => onSelectNode && onSelectNode(members[0].id) : undefined}
          >
            <div style={{ minWidth: 80, textAlign: 'right', color: '#666', fontSize: '12px', paddingTop: 2 }}>
              {yearLabel}
            </div>
            <div style={{ borderLeft: '2px solid #ccc', margin: '0 12px', alignSelf: 'stretch', minHeight: 20 }} />
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', paddingTop: 2 }}>
              <span
                style={{ fontSize: '13px', cursor: 'pointer', color: '#222' }}
                onClick={!isSingle ? (e) => { e.stopPropagation(); onSelectNode && onSelectNode(rep.id) } : undefined}
              >
                {rep.nameKo || rep.title}
              </span>
              {!isSingle && (
                <button
                  style={{ fontSize: '11px', color: '#4a90d9', marginLeft: '8px', cursor: 'pointer', background: 'none', border: 'none', padding: '0' }}
                  onClick={(e) => {
                    e.stopPropagation()
                    setOpenGroup(openGroup === groupKey ? null : groupKey)
                  }}
                >
                  외 {members.length - 1}건
                </button>
              )}
              {openGroup === groupKey && (
                <div
                  style={{
                    position: 'absolute',
                    left: 104,
                    top: '100%',
                    backgroundColor: '#fff',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    padding: '4px 0',
                    zIndex: 100,
                    minWidth: '200px',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                  }}
                  onClick={e => e.stopPropagation()}
                >
                  {members.map(ev => (
                    <div
                      key={ev.id}
                      style={{ padding: '4px 12px', fontSize: '13px', cursor: 'pointer', color: '#222' }}
                      onClick={() => { onSelectNode && onSelectNode(ev.id); setOpenGroup(null) }}
                    >
                      {ev.nameKo || ev.title}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default TimelineView
