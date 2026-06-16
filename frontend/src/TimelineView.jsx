import { useEffect, useRef, useState } from 'react'
import { BookOpen } from 'lucide-react'
import { SELECT_HL } from './theme'
import { apiGet } from './api'

const BOOK_COLOR = '#a78bfa'

function fmtYear(y) {
  return y == null ? '?' : (y < 0 ? `BC ${-y}` : `AD ${y}`)
}

function sortKeyToYear(sortKey) {
  // sortKey는 연도 정수(BC = 음수)로 저장된다고 가정
  return typeof sortKey === 'number' ? sortKey : null
}

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
  const [books, setBooks] = useState([])
  const [error, setError] = useState(false)
  const [openGroup, setOpenGroup] = useState(null)
  // 다권 사건에서 근거 권 목록을 펼친 사건의 id(인라인 확장). 한 번에 하나만 펼침.
  const [openBookList, setOpenBookList] = useState(null)
  // 어떤 bookFilter에 대해 "닫기"를 눌렀는지 식별자로 추적 — 새 필터(다른 참조)면 자동으로 다시 표시(effect 불필요).
  const [dismissedFilter, setDismissedFilter] = useState(null)
  const containerRef = useRef(null)

  useEffect(() => {
    apiGet('/events')
      .then(data => setEvents(data))
      .catch(() => setError(true))
  }, [])

  // 성경 66권(연도 가진 것만) — 타임라인 시대순 마커. 실패해도 사건 타임라인은 유지.
  useEffect(() => {
    apiGet('/books')
      .then(data => setBooks(data))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (openGroup === null && openBookList === null) return
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpenGroup(null)
        setOpenBookList(null)
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [openGroup, openBookList])

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

  const activeFilter = bookFilter && dismissedFilter !== bookFilter ? bookFilter : null
  const inFilter = (y) => {
    if (!activeFilter) return true
    if (y === null) return false
    if (activeFilter.startYear != null && y < activeFilter.startYear) return false
    if (activeFilter.endYear != null && y > activeFilter.endYear) return false
    return true
  }
  const visibleGroups = groups.filter(g => inFilter(sortKeyToYear(g.sortKey)))

  // 사건 그룹 + 성경 책 마커를 연도순으로 합친 통합 타임라인.
  // 단독 책 마커는 사건 없는 31권(yearApprox=true)만 — 사건 있는 35권은 단독 행 대신
  // 각 사건의 근거 권 칩으로 표시(ADR-0002). 두 집합은 startYear 유무로 겹치지 않는다.
  const timeline = [
    ...visibleGroups.map(g => ({ kind: 'group', sortKey: g.sortKey, group: g })),
    ...books.filter(b => b.yearApprox && inFilter(b.startYear)).map(b => ({ kind: 'book', sortKey: b.startYear, book: b })),
  ].sort((a, b) => a.sortKey - b.sortKey)

  // 사건의 근거 권 칩. 1권: 클릭→그 권 패널. 2~4권: 클릭→첫 권 디폴트 오픈 + 권 목록 인라인 펼침,
  // 목록의 다른 권 클릭 시 전환. (인라인 확장 — 부모 overflow/팝오버 안에서도 잘림 없음)
  const chipBase = {
    display: 'inline-flex', alignItems: 'center', gap: 3,
    fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
    border: `1px solid ${BOOK_COLOR}`, cursor: 'pointer', fontWeight: 600,
    background: 'rgba(167,139,250,0.10)', color: '#5b21b6',
  }
  const renderBookChip = (ev) => {
    const bks = ev.books || []
    if (bks.length === 0) return null
    const first = bks[0]
    if (bks.length === 1) {
      const sel = selectedNode === first.id
      return (
        <button
          title={`근거: ${first.nameKo || first.name}`}
          onClick={(e) => { e.stopPropagation(); onSelectNode && onSelectNode(first.id) }}
          style={{ ...chipBase, marginLeft: 6, ...(sel ? { background: BOOK_COLOR, color: '#fff' } : null) }}
        >📖 {first.nameKo || first.name}</button>
      )
    }
    const expanded = openBookList === ev.id
    const anySel = bks.some(b => b.id === selectedNode)
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', flexWrap: 'wrap', gap: 4, marginLeft: 6 }}>
        <button
          title={`근거 ${bks.length}권`}
          onClick={(e) => {
            e.stopPropagation()
            if (expanded) { setOpenBookList(null) }
            else { setOpenBookList(ev.id); onSelectNode && onSelectNode(first.id) }
          }}
          style={{ ...chipBase, ...(anySel ? { background: BOOK_COLOR, color: '#fff' } : null) }}
        >📖 {first.nameKo || first.name} 외 {bks.length - 1}권 {expanded ? '▾' : '▸'}</button>
        {expanded && bks.map(b => {
          const sel = selectedNode === b.id
          return (
            <button
              key={b.id}
              onClick={(e) => { e.stopPropagation(); onSelectNode && onSelectNode(b.id) }}
              style={{ ...chipBase, background: sel ? BOOK_COLOR : '#fff', color: sel ? '#fff' : '#5b21b6' }}
            >{b.nameKo || b.name}</button>
          )
        })}
      </span>
    )
  }

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
            onClick={() => setDismissedFilter(bookFilter)}
            style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#1a3a8f', fontSize: 13, padding: '0 4px' }}
          >× 닫기</button>
        </div>
      )}
      {timeline.map((item) => {
        if (item.kind === 'book') {
          const b = item.book
          const isSel = selectedNode === b.id
          return (
            <div
              key={'book-' + b.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                padding: '4px 8px',
                minHeight: '28px',
                backgroundColor: isSel ? SELECT_HL : 'rgba(167,139,250,0.07)',
                cursor: 'pointer',
                position: 'relative',
              }}
              onClick={() => onSelectNode && onSelectNode(b.id)}
            >
              <div style={{ minWidth: 80, textAlign: 'right', color: '#666', fontSize: '12px', paddingTop: 2 }}>
                {fmtYear(b.startYear)}
              </div>
              <div style={{ borderLeft: `2px ${b.yearApprox ? 'dashed' : 'solid'} ${BOOK_COLOR}`, margin: '0 12px', alignSelf: 'stretch', minHeight: 20 }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', paddingTop: 1 }}>
                <BookOpen size={14} style={{ color: BOOK_COLOR, flexShrink: 0 }} />
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#5b21b6' }}>{b.nameKo || b.name}</span>
                <span style={{ fontSize: '13px', color: BOOK_COLOR, fontWeight: 700 }}>+</span>
                {b.yearApprox && (
                  <span
                    title={b.yearBasis || '추정 연도'}
                    style={{ fontSize: 10, color: '#8b80a8', border: `1px dashed ${BOOK_COLOR}`, borderRadius: 4, padding: '0 4px' }}
                  >추정</span>
                )}
              </div>
            </div>
          )
        }

        const { startDate, members, rep } = item.group
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
              {renderBookChip(rep)}
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
                      style={{ padding: '4px 12px', fontSize: '13px', color: '#222', display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}
                    >
                      <span
                        style={{ cursor: 'pointer' }}
                        onClick={() => { onSelectNode && onSelectNode(ev.id); setOpenGroup(null) }}
                      >{ev.nameKo || ev.title}</span>
                      {renderBookChip(ev)}
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
