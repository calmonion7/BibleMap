import { useEffect, useRef, useState } from 'react'
import { SELECT_HL } from './theme'

function fmtYear(y) {
  return y == null ? '?' : (y < 0 ? `BC ${-y}` : `AD ${y}`)
}

function sortKeyToYear(sortKey) {
  // sortKey는 연도 정수(BC = 음수)로 저장된다고 가정
  return typeof sortKey === 'number' ? sortKey : null
}

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

function TimelineView({ onSelectNode, selectedNode, bookFilter }) {
  const [events, setEvents] = useState([])
  const [error, setError] = useState(false)
  const [openGroup, setOpenGroup] = useState(null)
  const [filterDismissed, setFilterDismissed] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => { setFilterDismissed(false) }, [bookFilter])

  useEffect(() => {
    fetch(`${API_URL}/events`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => setEvents(data))
      .catch(() => setError(true))
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
      const sortKey = members[0].sortKey ?? 0
      const rep = members.find(e => e.nameKo) || members[0]
      return { startDate, members, sortKey, rep }
    })
    .sort((a, b) => {
      if (a.sortKey < b.sortKey) return -1
      if (a.sortKey > b.sortKey) return 1
      return 0
    })

  const activeFilter = bookFilter && !filterDismissed ? bookFilter : null
  const visibleGroups = activeFilter
    ? groups.filter(g => {
        const y = sortKeyToYear(g.sortKey)
        if (y === null) return false
        if (activeFilter.startYear != null && y < activeFilter.startYear) return false
        if (activeFilter.endYear != null && y > activeFilter.endYear) return false
        return true
      })
    : groups

  if (error) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa', color: '#999', fontSize: 14 }}>
        사건을 불러오지 못했습니다
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', overflowY: 'auto', background: '#fafafa', position: 'relative', paddingTop: 16 }}
    >
      {activeFilter && (
        <div style={{
          position: 'sticky', top: 0, zIndex: 10,
          display: 'flex', alignItems: 'center', gap: 8,
          background: '#e8f0fe', borderBottom: '1px solid #c5d5fb',
          padding: '6px 12px', fontSize: 12, color: '#1a3a8f',
        }}>
          <span>{activeFilter.nameKo} 범위: {fmtYear(activeFilter.startYear)} ~ {fmtYear(activeFilter.endYear)}</span>
          <button
            onClick={() => setFilterDismissed(true)}
            style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#1a3a8f', fontSize: 13, padding: '0 4px' }}
          >× 닫기</button>
        </div>
      )}
      {visibleGroups.map(({ startDate, members, rep }) => {
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
              backgroundColor: isSelected ? SELECT_HL : 'transparent',
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
