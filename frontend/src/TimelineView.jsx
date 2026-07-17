import { useEffect, useMemo, useRef, useState } from 'react'
import { SELECT_HL, TYPE_COLOR } from './theme'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'
import { parseYear } from './dates'

const BOOK_COLOR = TYPE_COLOR.Book

// 시대 밴드(task#200) — ADR-0014 보수 연대 기반 연도 경계, persons.py _ERA_ORDER 8구간과 정합.
// 경계 근거: 아브라함 출생 BC 2166 · 야곱 애굽 이주 BC 1876 · 사사기 시작 BC 1375 ·
// 사울 즉위 BC 1050 · 왕국 분열 BC 930 · 예루살렘 함락 BC 586 · 예수 탄생 BC 5경.
const ERA_BANDS = [
  { name: '원시사', from: -Infinity, range: '창조 – BC 2166' },
  { name: '족장', from: -2166, range: 'BC 2166 – 1876' },
  { name: '출애굽·정복', from: -1876, range: 'BC 1876 – 1375' },
  { name: '사사', from: -1375, range: 'BC 1375 – 1050' },
  { name: '왕국', from: -1050, range: 'BC 1050 – 930' },
  { name: '선지자', from: -930, range: 'BC 930 – 586' },
  { name: '포로', from: -586, range: 'BC 586 – 5' },
  { name: '신약', from: -5, range: 'BC 5 –' },
]
const eraOf = (y) => {
  let band = ERA_BANDS[0]
  for (const b of ERA_BANDS) { if (y >= b.from) band = b }
  return band
}

function fmtYear(y) {
  return y == null ? '?' : (y < 0 ? `BC ${-y}` : `AD ${y}`)
}

function sortKeyToYear(sortKey) {
  // sortKey는 연도 정수(BC = 음수)로 저장된다고 가정
  return typeof sortKey === 'number' ? sortKey : null
}

function TimelineView({ onSelectNode, selectedNode, bookFilter, personFilter, personName, verseLang, setVerseLang }) {
  // personFilter는 Set이어야 한다(.has() 호출). Array를 넘기면 런타임 크래시 — dev에서 조기 경고.
  if (import.meta.env.DEV && personFilter != null && !(personFilter instanceof Set))
    console.error('TimelineView: personFilter must be a Set, got', personFilter)
  const [events, setEvents] = useState([])
  const [error, setError] = useState(false)
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
  const [dismissedPersonFilter, setDismissedPersonFilter] = useState(null)
  const containerRef = useRef(null)
  const groupRefs = useRef({})

  useEffect(() => {
    apiGet('/events')
      .then(data => setEvents(data))
      .catch(() => setError(true))
  }, [])

  useEffect(() => {
    if (!selectedNode || events.length === 0) return
    const ev = events.find(e => e.id === selectedNode)
    if (!ev) return
    const key = ev.startDate ?? ''
    const raf = requestAnimationFrame(() => {
      groupRefs.current[key]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
    return () => cancelAnimationFrame(raf)
  }, [selectedNode, events])

  useEffect(() => {
    if (verseView === null) return
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setVerseView(null)
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [verseView])

  const groups = useMemo(() => {
    const groupMap = new Map()
    for (const ev of events) {
      const key = ev.startDate ?? ''
      if (!groupMap.has(key)) groupMap.set(key, [])
      groupMap.get(key).push(ev)
    }
    return Array.from(groupMap.entries())
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
  }, [events])

  const activeFilter = bookFilter && dismissedFilter !== bookFilter ? bookFilter : null
  const activePersonFilter = personFilter && dismissedPersonFilter !== personFilter ? personFilter : null
  // 시대 밴드 섹션 — 필터 통과 그룹을 시간순으로 시대별 묶음(비는 시대는 자연 생략)
  const { sections } = useMemo(() => {
    const inFilter = (y) => {
      if (!activeFilter) return true
      if (y === null) return false
      if (activeFilter.startYear != null && y < activeFilter.startYear) return false
      if (activeFilter.endYear != null && y > activeFilter.endYear) return false
      return true
    }
    const vg = groups
      .filter(g => inFilter(sortKeyToYear(g.sortKey)))
      .filter(g => !activePersonFilter || g.members.some(ev => activePersonFilter.has(ev.id)))
      .sort((a, b) => a.sortKey - b.sortKey)
    const secs = []
    for (const g of vg) {
      const band = eraOf(sortKeyToYear(g.sortKey) ?? 0)
      if (!secs.length || secs[secs.length - 1].era !== band) secs.push({ era: band, groups: [] })
      secs[secs.length - 1].groups.push(g)
    }
    return { sections: secs }
  }, [groups, activeFilter, activePersonFilter])

  // 사건의 근거 권 칩. 클릭 → 그 사건 아래 인라인 구절 뷰 토글(권 선택 → 인용범위 → 절 본문).
  // 한 번에 한 사건만 펼침. (인라인 확장 — 플로팅 nav 바에 가리지 않게 absolute 팝오버 금지)
  const chipBase = {
    display: 'inline-flex', alignItems: 'center', gap: 3,
    fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
    border: `1px solid ${BOOK_COLOR}`, cursor: 'pointer', fontWeight: 600,
    background: 'var(--bg-2)', color: BOOK_COLOR,
  }
  // 구절 레이어 토글. 열 때 첫 권 선택 + /event/{id}/verses 1회 fetch(id로 묶어 stale 무시).
  // (기존 행 아래 인라인 아코디언은 모바일에서 리스트를 길게 밀어내 불편 — 관계 뷰 VerseLayer와 동일한 양피지 모달로 통일)
  const toggleVerseView = (ev) => {
    const bks = ev.books || []
    if (bks.length === 0) return
    if (verseView && verseView.eventId === ev.id) { setVerseView(null); openEventRef.current = null; return }
    openEventRef.current = ev.id
    setVerseView({ eventId: ev.id, event: ev, bookId: bks[0].id })
    setEventVerses({ id: ev.id, data: null })
    apiGet('/event/' + ev.id + '/verses')
      .then(data => { if (openEventRef.current === ev.id) setEventVerses({ id: ev.id, data }) })
      .catch(e => { if (openEventRef.current === ev.id) { console.warn('[Timeline] 사건 구절 로드 실패', e); setEventVerses({ id: ev.id, data: { books: [] } }) } })
  }

  // 다권 사건에서 권 탭 전환.
  const selectVerseBook = (bookId) => {
    setVerseView(prev => prev ? { ...prev, bookId } : prev)
  }

  const closeVerseView = () => { setVerseView(null); openEventRef.current = null }

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
        style={{ ...chipBase, marginLeft: 6, ...(open ? { background: BOOK_COLOR, color: 'var(--bg-0)' } : null) }}
      >📖 {label} {open ? '▾' : '▸'}</button>
    )
  }

  // 구절 레이어 — 스크롤 컨테이너의 형제(absolute inset 0)로 띄우는 양피지 모달 (RelationsView VerseLayer 패턴).
  const renderVerseLayer = () => {
    if (!verseView) return null
    const ev = verseView.event
    const overlay = eventVerses.id === ev.id ? eventVerses.data : null
    const nameById = new Map((ev.books || []).map(b => [b.id, b.nameKo || b.name]))
    const ovBooks = overlay ? (overlay.books || []) : []
    const selBook = ovBooks.find(b => b.bookId === verseView.bookId) || ovBooks[0]
    const selName = selBook ? (nameById.get(selBook.bookId) || '') : ''
    return (
      <div
        onClick={closeVerseView}
        // 모달 스크림 — 전용 토큰 없어 값 유지(다크 배경 위 반투명 오버레이라 무해)
        style={{ position: 'absolute', inset: 0, zIndex: 100, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
      >
        {/* 근거 구절 모달 = 양피지 카드(원칙 2) */}
        <div onClick={e => e.stopPropagation()} style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontWeight: 700, fontSize: 15, flex: 1, fontFamily: 'var(--serif)' }}>{ev.nameKo || ev.title}</span>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            <button onClick={closeVerseView} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
          </div>
          {ovBooks.length > 1 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
              {ovBooks.map(b => {
                const sel = b.bookId === selBook.bookId
                return (
                  <button
                    key={b.bookId}
                    onClick={() => selectVerseBook(b.bookId)}
                    style={{ ...chipBase, background: sel ? BOOK_COLOR : 'transparent', color: sel ? 'var(--bg-0)' : 'var(--paper-accent)', borderColor: 'var(--paper-accent)' }}
                  >{nameById.get(b.bookId) || b.bookId}</button>
                )
              })}
            </div>
          )}
          {overlay === null ? (
            <div style={{ padding: '12px 0' }}><Spinner size={20} color="var(--paper-accent)" /></div>
          ) : ovBooks.length === 0 ? (
            <div style={{ fontSize: 13, padding: '8px 0' }}>표시할 구절이 없습니다</div>
          ) : (
            <>
              <div style={{ fontSize: 12, color: 'var(--paper-accent)', marginBottom: 8 }}>{selName} {selBook.rangeLabel}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {selBook.verses.map(v => {
                  const body = (verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'
                  return (
                    <div key={v.verseID} style={{ fontSize: 15, color: 'var(--paper-ink)', fontFamily: 'var(--serif)', lineHeight: 1.8 }}>
                      <span style={{ fontWeight: 600, color: 'var(--paper-accent)', marginRight: 6, fontSize: 12 }}>{v.chapter}:{v.verse}</span>
                      {body}
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-0)', color: 'var(--ink-faint)', fontSize: 14 }}>
        사건을 불러오지 못했습니다
      </div>
    )
  }

  // 연도 칸 반응형 폭 — 데스크톱 96px, 모바일은 뷰포트 비례(레일 위치는 같은 변수로 정렬)
  const YEAR_W = 'clamp(78px, 21vw, 96px)'

  // 필터 배너 — 스크롤 밖 상단 고정(시대 sticky 헤더와 겹침 없음), 금색 포인트
  const renderBanner = (label, onClose) => (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      background: 'var(--bg-1)', borderBottom: '1px solid var(--line)', borderLeft: '3px solid var(--gold-dim)',
      padding: '6px 12px', fontSize: 12, color: 'var(--ink-dim)',
    }}>
      <span>{label}</span>
      <button
        onClick={onClose}
        style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink-dim)', fontSize: 13, padding: '0 4px' }}
      >× 닫기</button>
    </div>
  )

  return (
    // 비스크롤 루트(세로 flex: 배너 + 스크롤 리스트) + 구절 레이어 형제 — 모달을 overflow:auto 자식에 두면 오배치(회고 선례)
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: 'var(--bg-0)', WebkitTapHighlightColor: 'transparent', display: 'flex', flexDirection: 'column' }}>
    {activeFilter && renderBanner(`${activeFilter.nameKo} 범위: ${fmtYear(activeFilter.startYear)} ~ ${fmtYear(activeFilter.endYear)}`, () => setDismissedFilter(bookFilter))}
    {activePersonFilter && renderBanner(`${personName}이 언급된 사건`, () => setDismissedPersonFilter(personFilter))}
    <div
      ref={containerRef}
      style={{ width: '100%', flex: 1, minHeight: 0, boxSizing: 'border-box', overflowY: 'auto', position: 'relative', paddingBottom: 48 }}
    >
      {sections.map((sec) => (
        <div key={sec.era.name}>
          {/* 시대 밴드 헤더 — sticky(배너가 스크롤 밖이라 top:0 충돌 없음) */}
          <div style={{
            position: 'sticky', top: 0, zIndex: 10,
            display: 'flex', alignItems: 'baseline', gap: 8,
            background: 'var(--bg-0)', borderBottom: '1px solid var(--line)',
            padding: '10px 12px 6px',
          }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: 'var(--gold)', letterSpacing: '0.05em' }}>{sec.era.name}</span>
            <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{sec.era.range}</span>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{sec.groups.reduce((n, g) => n + g.members.length, 0)}</span>
          </div>
          {/* 섹션 본문 — 연속 세로 레일 위 사건 도트 */}
          <div style={{ position: 'relative', padding: '6px 0' }}>
            <span style={{ position: 'absolute', top: 0, bottom: 0, left: `calc(${YEAR_W} + 8px + 9px)`, width: 2, background: 'var(--line)' }} />
            {sec.groups.map((group) => {
              const { startDate, members, rep } = group
              const isSelected = selectedNode && members.some(e => e.id === selectedNode)
              const isAuthored = rep.authored === true
              const yearLabel = isAuthored && rep.yearLabel ? rep.yearLabel : parseYear(startDate)
              const groupKey = startDate

              return (
                <div key={groupKey} ref={el => { groupRefs.current[groupKey] = el }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    padding: '4px 8px',
                    minHeight: '28px',
                    backgroundColor: isSelected ? SELECT_HL : 'transparent',
                    position: 'relative',
                  }}
                >
                  {/* 연도 칸은 고정 폭 — minWidth만 주면 긴 라벨(태초 무렵 (전통 BC 4000경) 등)이 행마다 폭을 늘려 제목 시작점이 어긋난다. 긴 라벨은 줄바꿈. */}
                  <div style={{ width: YEAR_W, flexShrink: 0, textAlign: 'right', color: 'var(--ink-faint)', fontSize: '11.5px', lineHeight: 1.35, paddingTop: 3 }}>
                    {/* 연대추정 표기는 yearLabel의 '경' 접미가 담당 — '~' 중복 표기는 뺀다 */}
                    {isAuthored ? <span title="연대추정 (저작 배경 기준)">{yearLabel}</span> : yearLabel}
                  </div>
                  {/* 레일 도트 — 섹션 연속 레일 위, 선택 시 금색 */}
                  <div style={{ width: 20, flexShrink: 0, display: 'flex', justifyContent: 'center', paddingTop: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: isSelected ? 'var(--gold)' : 'var(--line-strong)', boxShadow: '0 0 0 3px var(--bg-0)', position: 'relative', zIndex: 1 }} />
                  </div>
                  {/* 같은 날짜의 사건들을 모두 인라인 표시 — 플로팅 그룹 팝업(외 N건) 제거, 각 사건이 직접 클릭 가능 */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3, paddingTop: 2, minWidth: 0, paddingLeft: 4 }}>
                    {members.map(ev => (
                      <div key={ev.id} style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
                        <span
                          style={{ fontSize: '13px', cursor: 'pointer', color: 'var(--ink)' }}
                          onClick={(e) => { e.stopPropagation(); onSelectNode && onSelectNode(ev.id) }}
                        >
                          {ev.nameKo || ev.title}
                        </span>
                        {renderBookChip(ev)}
                      </div>
                    ))}
                  </div>
                </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
    {renderVerseLayer()}
    </div>
  )
}

export default TimelineView
