import { useEffect, useMemo, useRef, useState } from 'react'
import { BookOpen } from 'lucide-react'
import { SELECT_HL, TYPE_COLOR } from './theme'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'

const BOOK_COLOR = '#a78bfa'
const EVENT_COLOR = TYPE_COLOR.Event

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

function TimelineView({ onSelectNode, selectedNode, bookFilter, verseLang, setVerseLang }) {
  const [events, setEvents] = useState([])
  const [books, setBooks] = useState([])
  const [error, setError] = useState(false)
  const [openGroup, setOpenGroup] = useState(null)
  // 근거 구절 인라인 뷰를 펼친 사건 — { eventId, bookId, expanded } (한 번에 하나만).
  // bookId: 선택된 권(다권이면 탭 전환). expanded: 선택 권의 절 본문을 펼쳤는지(▾).
  const [verseView, setVerseView] = useState(null)
  // 열린 사건의 /event/{id}/verses 응답 — { id, data }(id로 묶어 stale 무시, 로딩 중 data=null).
  // 응답의 각 절에 textKo/textEn이 미리저장돼 있어 본문은 추가 fetch 없이 표시한다(ADR-0003).
  const [eventVerses, setEventVerses] = useState({ id: null, data: null })
  // 현재 열린 사건 id. /event/{id}/verses 응답이 늦게 와도(out-of-order) 더 최근에 연 사건의
  // 상태를 덮어쓰지 않도록, 응답 커밋 전에 이 ref와 대조한다.
  const openEventRef = useRef(null)
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

  // eventId → 사건. 책 마커 행의 연결 사건 칩(book.events는 id 배열)을 이름·클릭으로 풀기 위함.
  const eventById = useMemo(() => new Map(events.map(e => [e.id, e])), [events])

  useEffect(() => {
    if (openGroup === null && verseView === null) return
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpenGroup(null)
        setVerseView(null)
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [openGroup, verseView])

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

  // 사건의 근거 권 칩. 클릭 → 그 사건 아래 인라인 구절 뷰 토글(권 선택 → 인용범위 → 절 본문).
  // 한 번에 한 사건만 펼침. (인라인 확장 — 플로팅 nav 바에 가리지 않게 absolute 팝오버 금지)
  const chipBase = {
    display: 'inline-flex', alignItems: 'center', gap: 3,
    fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
    border: `1px solid ${BOOK_COLOR}`, cursor: 'pointer', fontWeight: 600,
    background: 'rgba(167,139,250,0.10)', color: '#5b21b6',
  }
  const verseBoxStyle = {
    margin: '4px 0 6px 104px', padding: '8px 12px',
    background: '#f5f3ff', borderLeft: `3px solid ${BOOK_COLOR}`, borderRadius: 6,
    fontSize: 12,
  }
  // 책 마커 행의 연결 사건 칩. chipBase와 같은 형태에 Event 색(theme.js). 클릭 → 그 사건 선택.
  const eventChipStyle = {
    display: 'inline-flex', alignItems: 'center', gap: 3,
    fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
    border: `1px solid ${EVENT_COLOR}`, cursor: 'pointer', fontWeight: 600,
    background: 'rgba(245,166,35,0.12)', color: '#a85d00',
  }

  // 사건의 인라인 구절 뷰 토글. 열 때 첫 권 선택 + /event/{id}/verses 1회 fetch(id로 묶어 stale 무시).
  const toggleVerseView = (ev) => {
    const bks = ev.books || []
    if (bks.length === 0) return
    if (verseView && verseView.eventId === ev.id) { setVerseView(null); openEventRef.current = null; return }
    openEventRef.current = ev.id
    setVerseView({ eventId: ev.id, bookId: bks[0].id, expanded: false })
    setEventVerses({ id: ev.id, data: null })
    apiGet('/event/' + ev.id + '/verses')
      .then(data => { if (openEventRef.current === ev.id) setEventVerses({ id: ev.id, data }) })
      .catch(() => { if (openEventRef.current === ev.id) setEventVerses({ id: ev.id, data: { books: [] } }) })
  }

  // 다권 사건에서 권 탭 전환(절 본문 펼침은 초기화).
  const selectVerseBook = (bookId) => {
    setVerseView(prev => prev ? { ...prev, bookId, expanded: false } : prev)
  }

  // 절 본문 펼침/접힘 토글. 본문(textKo/textEn)은 /event/{id}/verses에 미리저장돼 추가 fetch 없음.
  const toggleVerseText = () => {
    if (!verseView) return
    setVerseView({ ...verseView, expanded: !verseView.expanded })
  }

  const renderBookChip = (ev) => {
    const bks = ev.books || []
    if (bks.length === 0) return null
    const first = bks[0]
    const open = verseView != null && verseView.eventId === ev.id
    const label = bks.length === 1
      ? first.nameKo || first.name
      : `${first.nameKo || first.name} 외 ${bks.length - 1}권`
    return (
      <button
        title={bks.length === 1 ? `근거: ${first.nameKo || first.name}` : `근거 ${bks.length}권`}
        onClick={(e) => { e.stopPropagation(); toggleVerseView(ev) }}
        style={{ ...chipBase, marginLeft: 6, ...(open ? { background: BOOK_COLOR, color: '#fff' } : null) }}
      >📖 {label} {open ? '▾' : '▸'}</button>
    )
  }

  // 사건 행 아래 인라인 구절 뷰. ev.books로 권 이름을, /event/{id}/verses로 인용범위·절을 표시.
  const renderVerseView = (ev) => {
    if (!verseView || verseView.eventId !== ev.id) return null
    const overlay = eventVerses.id === ev.id ? eventVerses.data : null
    if (overlay === null) {
      return <div style={{ ...verseBoxStyle, color: '#8b80a8' }}>구절을 불러오는 중…</div>
    }
    const ovBooks = overlay.books || []
    if (ovBooks.length === 0) {
      return <div style={{ ...verseBoxStyle, color: '#8b80a8' }}>표시할 구절이 없습니다</div>
    }
    const nameById = new Map((ev.books || []).map(b => [b.id, b.nameKo || b.name]))
    const selBook = ovBooks.find(b => b.bookId === verseView.bookId) || ovBooks[0]
    const selName = nameById.get(selBook.bookId) || ''
    return (
      <div style={verseBoxStyle} onClick={e => e.stopPropagation()}>
        {ovBooks.length > 1 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
            {ovBooks.map(b => {
              const sel = b.bookId === selBook.bookId
              return (
                <button
                  key={b.bookId}
                  onClick={() => selectVerseBook(b.bookId)}
                  style={{ ...chipBase, background: sel ? BOOK_COLOR : '#fff', color: sel ? '#fff' : '#5b21b6' }}
                >{nameById.get(b.bookId) || b.bookId}</button>
              )
            })}
          </div>
        )}
        <button
          onClick={() => toggleVerseText()}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            border: 'none', background: 'none', cursor: 'pointer', padding: 0, font: 'inherit',
            fontSize: 12, fontWeight: 600, color: '#5b21b6',
          }}
        >
          {selName} {selBook.rangeLabel}
          <span style={{ fontSize: 10 }}>{verseView.expanded ? '▾' : '▸'}</span>
        </button>
        {verseView.expanded && (
          <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 5 }}>
            <div>
              <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color={BOOK_COLOR} />
            </div>
            {selBook.verses.map(v => {
              const body = (verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'
              return (
                <div key={v.verseID} style={{ fontSize: 12, color: '#374151', lineHeight: 1.5 }}>
                  <span style={{ fontWeight: 600, color: '#6d28d9', marginRight: 6 }}>{v.chapter}:{v.verse}</span>
                  {body}
                </div>
              )
            })}
          </div>
        )}
      </div>
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
      style={{ width: '100%', height: '100%', boxSizing: 'border-box', overflowY: 'auto', background: '#fafafa', position: 'relative', paddingTop: 16, paddingBottom: 48 }}
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
                backgroundColor: isSel ? SELECT_HL : 'transparent',
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
                {b.yearApprox && (
                  <span
                    title={b.yearBasis || '추정 연도'}
                    style={{ fontSize: 10, color: '#8b80a8', border: `1px dashed ${BOOK_COLOR}`, borderRadius: 4, padding: '0 4px' }}
                  >추정</span>
                )}
                {(() => {
                  const evs = (b.events || []).map(eid => eventById.get(eid)).filter(Boolean)
                  if (evs.length === 0) return null
                  const shown = evs.slice(0, 3)
                  const extra = evs.length - shown.length
                  return (
                    <>
                      <span
                        title="집필 배경·관련 사건 — 사건의 근거(📖)가 아닙니다"
                        style={{ fontSize: 10, color: '#8b80a8' }}
                      >배경</span>
                      {shown.map(ev => (
                        <button
                          key={ev.id}
                          title={`집필 배경·관련 사건 (근거 아님): ${ev.nameKo || ev.title}`}
                          onClick={(e) => { e.stopPropagation(); onSelectNode && onSelectNode(ev.id) }}
                          style={eventChipStyle}
                        >⚡ {ev.nameKo || ev.title}</button>
                      ))}
                      {extra > 0 && (
                        <span style={{ fontSize: 10, color: '#8b80a8' }}>외 {extra}건</span>
                      )}
                    </>
                  )
                })()}
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
          <div key={groupKey}>
          <div
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
          {renderVerseView(rep)}
          {members.filter(ev => ev.id !== rep.id).map(ev => <div key={'vv-' + ev.id}>{renderVerseView(ev)}</div>)}
          </div>
        )
      })}
    </div>
  )
}

export default TimelineView
