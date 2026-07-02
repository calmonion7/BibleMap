import { useState, useEffect, useRef } from 'react'
import { TYPE_COLOR, TYPE_KO } from './theme'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'
import { parseYear } from './dates'

const REL_KO = {
  PARENT_OF: '부모',
  CHILD_OF: '자녀',
  SIBLING_OF: '형제·자매',
  PARTNER_OF: '배우자',
  MEMBER_OF: '소속',
  HAS_PARTICIPANT: '참여',
  OCCURS_AT: '발생 장소',
  PART_OF: '상위 사건',
}

// 이웃 그룹핑 표시 순서(Unknown 포함 — 미매핑 타입도 묶는다). 색·한글 라벨은 theme.js 공유 팔레트.
const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Unknown']

function typeOf(label) {
  return TYPE_COLOR[label] ? label : 'Unknown'
}

// collapsed[key] !== false → 접힘(기본), false → 펼침
function SectionHeader({ label, color, count, sectionKey, collapsed, onToggle }) {
  const isOpen = collapsed[sectionKey] === false
  return (
    <button
      onClick={() => onToggle(sectionKey)}
      style={{
        display: 'flex', alignItems: 'center', gap: 6, width: '100%',
        border: 'none', background: 'none', cursor: 'pointer', padding: '0 4px 6px',
        fontSize: 12, fontWeight: 700, color: color ?? '#5a6481',
      }}
    >
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <span style={{ flex: 1, textAlign: 'left' }}>{label}</span>
      {count != null && <span style={{ color: '#aab2c5', fontWeight: 500 }}>{count}</span>}
      <span style={{ fontSize: 10, color: '#aab2c5', marginLeft: 2 }}>{isOpen ? '▾' : '▸'}</span>
    </button>
  )
}

function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false, onNodeLoaded, verseLang, setVerseLang, explorePersonId = null, onExplorePerson = () => {}, curatedIds = null, onExploreJourney = () => {} }) {
  // 어느 nodeId의 결과인지 id로 추적 — loading은 파생, stale 응답은 무시.
  // setState는 비동기 콜백에서만 호출(react-hooks set-state-in-effect 준수).
  const [state, setState] = useState({ id: null, node: null, error: null })
  const [collapsed, setCollapsed] = useState({})

  // Place 블록 — 사건 근거구절 인라인 드릴다운 (TimelineView 패턴 이식)
  // forNodeId 키로 nodeId 변경 시 자동 무효화 — effect 내 setState 없이 리셋(set-state-in-effect 준수).
  const [placeVerseViewRaw, setPlaceVerseView] = useState(null)   // { forNodeId, eventId, bookId, expanded } | null
  const placeVerseView = placeVerseViewRaw?.forNodeId === nodeId ? placeVerseViewRaw : null
  const [placeEventVerses, setPlaceEventVerses] = useState({ id: null, data: null })
  const placeOpenEventRef = useRef(null)

  // Place 블록 — 이 곳을 지난 다른 인물 칩: { forNodeId, persons } | null
  const [placePersonsState, setPlacePersonsState] = useState(null)
  const placePersons = placePersonsState?.forNodeId === nodeId ? placePersonsState.persons : null

  useEffect(() => {
    if (!nodeId) return
    let cancelled = false
    apiGet('/node/' + nodeId)
      .then(data => { if (!cancelled) {
        // Book은 전 섹션 기본 펼침 — 탭 0회로 모든 정보 도달(접기 토글은 유지, 노드 왕복에도 항상 펼침)
        setCollapsed(data.label === 'Book' ? {
          'book-central': false, 'book-themes': false, 'book-keyverse': false, 'book-background': false,
          'book-structure': false, 'book-keyppl': false, 'book-persons': false, 'book-events': false,
        } : {})
        setState({ id: nodeId, node: data, error: null }); onNodeLoaded?.(data)
      } })
      .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: e?.status ?? String(e) }) })
    return () => { cancelled = true }
  }, [nodeId, onNodeLoaded])

  // Place 블록 — 이 곳을 지난 큐레이션 인물 fetch
  useEffect(() => {
    if (!nodeId) return
    const node = state.id === nodeId ? state.node : null
    if (!node || node.label !== 'Place') return
    let cancelled = false
    const url = explorePersonId
      ? `/place/${nodeId}/curated-persons?exclude=${explorePersonId}`
      : `/place/${nodeId}/curated-persons`
    apiGet(url)
      .then(data => { if (!cancelled) setPlacePersonsState({ forNodeId: nodeId, persons: data.persons ?? [] }) })
      .catch(() => { if (!cancelled) setPlacePersonsState({ forNodeId: nodeId, persons: [] }) })
    return () => { cancelled = true }
  }, [nodeId, state.id, state.node, explorePersonId])

  const ready = state.id === nodeId
  const node = ready ? state.node : null
  const error = ready ? state.error : null

  const msgStyle = { padding: '1.25rem', fontSize: 14, color: '#7c8db0' }
  if (!nodeId) return <p style={msgStyle}>지도에서 마커를 클릭하세요</p>
  if (!ready) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}><Spinner color="rgba(100,120,180,0.6)" /></div>
  if (error) return <p style={{ ...msgStyle, color: '#dc3545' }}>불러오지 못했습니다 ({error})</p>

  // 이웃을 타입별로 그룹
  const groups = {}
  for (const n of node.neighbors) {
    const t = typeOf(n.label)
    if (!groups[t]) groups[t] = []
    groups[t].push(n)
  }

  const title = node.nameKoMissing ? `${node.name} (미번역)` : node.nameKo
  const subtitle = [
    !node.nameKoMissing && node.name !== node.nameKo ? node.name : null,
    TYPE_KO[node.label] || node.label,
  ].filter(Boolean).join(' · ')
  const headColor = TYPE_COLOR[typeOf(node.label)]
  // 대표 구절 본문 — 빌드타임 미리저장 필드(keyVerseTextKo/En)를 verseLang으로 선택(ADR-0003).
  const keyVerseText = node.label === 'Book'
    ? (verseLang === 'ko' ? node.properties.keyVerseTextKo : node.properties.keyVerseTextEn)
    : null
  const placeKeyVerseText = node.label === 'Place'
    ? (verseLang === 'ko' ? node.properties.keyVerseTextKo : node.properties.keyVerseTextEn)
    : null

  function toggle(key) {
    setCollapsed(prev => ({ ...prev, [key]: prev[key] === false }))
  }

  // Place 블록 — 사건 근거구절 드릴다운 헬퍼 (TimelineView 패턴 이식)
  const BOOK_COLOR = '#a78bfa'
  const placeChipBase = {
    display: 'inline-flex', alignItems: 'center', gap: 3,
    fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
    border: `1px solid ${BOOK_COLOR}`, cursor: 'pointer', fontWeight: 600,
    background: 'rgba(167,139,250,0.10)', color: '#5b21b6',
  }
  const placeVerseBoxStyle = {
    margin: '4px 0 6px 0', padding: '8px 12px',
    background: '#f5f3ff', borderLeft: `3px solid ${BOOK_COLOR}`, borderRadius: 6,
    fontSize: 12,
  }

  function togglePlaceVerseView(evId) {
    if (placeVerseView && placeVerseView.eventId === evId) {
      setPlaceVerseView(null); placeOpenEventRef.current = null; return
    }
    placeOpenEventRef.current = evId
    setPlaceVerseView({ forNodeId: nodeId, eventId: evId, bookId: null, expanded: false })
    setPlaceEventVerses({ id: evId, data: null })
    apiGet('/event/' + evId + '/verses')
      .then(data => {
        if (placeOpenEventRef.current !== evId) return
        // 첫 번째 권을 기본 선택
        const firstBookId = (data.books || [])[0]?.bookId ?? null
        setPlaceVerseView(prev => prev && prev.eventId === evId ? { ...prev, bookId: firstBookId } : prev)
        setPlaceEventVerses({ id: evId, data })
      })
      .catch(() => { if (placeOpenEventRef.current === evId) setPlaceEventVerses({ id: evId, data: { books: [] } }) })
  }

  function renderPlaceBookChip(evId) {
    const open = placeVerseView != null && placeVerseView.eventId === evId
    return (
      <button
        onClick={(e) => { e.stopPropagation(); togglePlaceVerseView(evId) }}
        style={{ ...placeChipBase, marginLeft: 6, ...(open ? { background: BOOK_COLOR, color: '#fff' } : null) }}
      >📖 구절 {open ? '▾' : '▸'}</button>
    )
  }

  function renderPlaceVerseView(evId) {
    if (!placeVerseView || placeVerseView.eventId !== evId) return null
    const overlay = placeEventVerses.id === evId ? placeEventVerses.data : null
    if (overlay === null) {
      return <div style={placeVerseBoxStyle}><Spinner size={20} color="rgba(107,40,217,0.5)" /></div>
    }
    const ovBooks = overlay.books || []
    if (ovBooks.length === 0) {
      return <div style={{ ...placeVerseBoxStyle, color: '#8b80a8' }}>표시할 구절이 없습니다</div>
    }
    const selBook = ovBooks.find(b => b.bookId === placeVerseView.bookId) || ovBooks[0]
    return (
      <div style={placeVerseBoxStyle} onClick={e => e.stopPropagation()}>
        {ovBooks.length > 1 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
            {ovBooks.map(b => {
              const sel = b.bookId === selBook.bookId
              return (
                <button
                  key={b.bookId}
                  onClick={() => setPlaceVerseView(prev => prev ? { ...prev, bookId: b.bookId, expanded: false } : prev)}
                  style={{ ...placeChipBase, background: sel ? BOOK_COLOR : '#fff', color: sel ? '#fff' : '#5b21b6' }}
                >{b.bookNameKo || b.bookId}</button>
              )
            })}
          </div>
        )}
        <button
          onClick={() => setPlaceVerseView(prev => prev ? { ...prev, expanded: !prev.expanded } : prev)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            border: 'none', background: 'none', cursor: 'pointer', padding: 0, font: 'inherit',
            fontSize: 12, fontWeight: 600, color: '#5b21b6',
          }}
        >
          {selBook.bookNameKo || selBook.bookId} {selBook.rangeLabel}
          <span style={{ fontSize: 10 }}>{placeVerseView.expanded ? '▾' : '▸'}</span>
        </button>
        {placeVerseView.expanded && (
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

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* 헤더 */}
      <div style={{
        padding: '14px 44px 14px 16px',
        borderBottom: '1px solid #eef0f5',
        position: 'sticky', top: 0, background: 'white', zIndex: 1,
      }}>
        {canGoBack && (
          <button
            onClick={onBack}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              border: 'none', background: 'none', cursor: 'pointer',
              color: '#7c8db0', fontSize: 13, padding: 0, marginBottom: 8, font: 'inherit',
            }}
          >← 뒤로</button>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: headColor, flexShrink: 0 }} />
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#1a1a2e', lineHeight: 1.3 }}>{title}</h2>
        </div>
        <div style={{ fontSize: 12, color: '#7c8db0', marginTop: 3, marginLeft: 18 }}>{subtitle}</div>
      </div>

      {/* Person 여정 탐험 CTA — 큐레이션 인물만, 현재 탐험 중인 인물 제외 */}
      {node.label === 'Person' && curatedIds?.has(node.id) && node.id !== explorePersonId && (
        <div style={{ margin: '12px 12px 0' }}>
          <button
            onClick={() => onExploreJourney(node.id)}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: 'none', cursor: 'pointer', font: 'inherit',
              fontSize: 13, fontWeight: 700, color: '#fff',
              background: TYPE_COLOR.Person,
            }}
          >
            🗺 {node.nameKo}의 여정 탐험 — 지도에서 보기
          </button>
        </div>
      )}

      {/* Person 인물 성품 섹션 — 이웃 그룹보다 위 */}
      {node.label === 'Person' && node.properties?.traits?.length > 0 && (
        <div style={{
          margin: '12px 12px 0', padding: '12px', borderRadius: 8,
          background: '#f8faff', border: '1px solid #e8ecf8',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 10 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Person }}>인물 성품</div>
            <span style={{ marginLeft: 'auto' }}>
              <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color={TYPE_COLOR.Person} />
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {node.properties.traits.map((t, i) => {
              const open = collapsed['trait-' + i] === false
              const verseText = verseLang === 'ko' ? t.verse_textKo : t.verse_textEn
              return (
              <div key={i}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600, color: '#1a1a2e',
                    background: 'rgba(124,156,252,0.12)', borderRadius: 4, padding: '2px 8px',
                  }}>{t.trait}</span>
                  <button
                    onClick={() => toggle('trait-' + i)}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 3,
                      border: 'none', background: 'none', cursor: 'pointer', padding: 0,
                      font: 'inherit', fontSize: 10, color: '#9aa5b8',
                    }}
                  >
                    {t.verse_ref}
                    <span style={{ fontSize: 9 }}>{open ? '▾' : '▸'}</span>
                  </button>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#5a6481', lineHeight: 1.5 }}>{t.description}</p>
                {open && (
                  <div style={{
                    marginTop: 5, padding: '7px 10px', background: '#eef2ff',
                    borderLeft: `3px solid ${TYPE_COLOR.Person}`, borderRadius: 6,
                    fontSize: 12, color: '#374151', lineHeight: 1.5,
                  }}>
                    {verseText || <span style={{ color: '#9aa5b8' }}>원문이 없습니다</span>}
                  </div>
                )}
              </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Book 전용 뷰 */}
      {node.label === 'Book' && (
        <div style={{ padding: '12px 16px 20px', fontSize: 14 }}>
          {/* 메타 칩 */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
            {[node.properties.testament, node.properties.genre,
              node.properties.startYear && `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC`,
              node.properties.chapterCount && `${node.properties.chapterCount}장`,
              node.properties.verseCount && `${node.properties.verseCount}절`,
              node.properties.authorKo && node.properties.writtenDate && `${node.properties.authorKo} · ${node.properties.writtenDate}`]
              .filter(Boolean).map((chip, i) => (
              <span key={i} style={{
                fontSize: 11, padding: '3px 8px', borderRadius: 999,
                background: '#eef0f5', color: '#5a6481',
              }}>{chip}</span>
            ))}
          </div>

          {/* 중심 메시지 — 책의 정수(1~2줄)를 최상단에 */}
          {node.properties.centralMessage && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="중심 메시지" color="#a78bfa" sectionKey="book-central" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-central'] === false && (
                <div style={{
                  padding: '10px 12px', background: '#f5f3ff', borderRadius: 8,
                  borderLeft: '3px solid #a78bfa', marginBottom: 4,
                  fontSize: 13, color: '#374151', lineHeight: 1.6,
                }}>{node.properties.centralMessage}</div>
              )}
            </div>
          )}

          {/* 성경 주제 */}
          {node.properties.themes?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="핵심 주제" color="#a78bfa" sectionKey="book-themes" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-themes'] === false && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', paddingBottom: 4 }}>
                  {node.properties.themes.map((t, i) => (
                    <span key={i} style={{
                      fontSize: 12, padding: '4px 10px', borderRadius: 999,
                      border: '1px solid #a78bfa', color: '#a78bfa',
                    }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 대표 구절 */}
          {node.properties.keyVerse && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="대표 구절" color="#a78bfa" sectionKey="book-keyverse" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-keyverse'] === false && (
                <div style={{
                  padding: '10px 12px', background: '#f5f3ff', borderRadius: 8,
                  borderLeft: '3px solid #a78bfa', marginBottom: 4,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: keyVerseText ? 4 : 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#6d28d9' }}>
                      {node.properties.keyVerse}
                    </div>
                    <span style={{ marginLeft: 'auto' }}>
                      <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color="#a78bfa" />
                    </span>
                  </div>
                  {keyVerseText && (
                    <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{keyVerseText}</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 시대적 배경 — 긴 산문은 정수 아래로 */}
          {node.properties.background && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="시대적 배경" color="#a78bfa" sectionKey="book-background" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-background'] === false && (
                <p style={{ margin: '0 0 4px', color: '#374151', lineHeight: 1.6 }}>{node.properties.background}</p>
              )}
            </div>
          )}

          {/* 구조 개요 */}
          {node.properties.structure && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="구조 개요" color="#a78bfa" sectionKey="book-structure" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-structure'] === false && (
                <p style={{ margin: '0 0 4px', color: '#374151', lineHeight: 1.6, fontSize: 13 }}>{node.properties.structure}</p>
              )}
            </div>
          )}

          {/* 핵심 인물 — 클릭 가능한 '주요 인물'(topPersons)이 있으면 중복이라 숨김(없는 34권에선 유일한 인물 정보) */}
          {node.properties.keyPeople?.length > 0 && !(node.topPersons?.length > 0) && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="핵심 인물" color="#a78bfa" sectionKey="book-keyppl" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-keyppl'] === false && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', paddingBottom: 4 }}>
                  {node.properties.keyPeople.map((p, i) => (
                    <span key={i} style={{
                      fontSize: 12, padding: '4px 10px', borderRadius: 999,
                      background: '#eef0f5', color: '#5a6481',
                    }}>{p}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 주요 인물 */}
          {node.topPersons?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="주요 인물" color={TYPE_COLOR.Person} count={node.topPersons.length} sectionKey="book-persons" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-persons'] === false && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingBottom: 4 }}>
                  {node.topPersons.map(p => (
                    <button key={p.id} onClick={() => onSelectNode(p.id)} style={{
                      display: 'flex', alignItems: 'center',
                      width: '100%', textAlign: 'left', font: 'inherit',
                      border: 'none', background: 'none', cursor: 'pointer',
                      borderLeft: `3px solid ${TYPE_COLOR.Person}`,
                      borderRadius: 6, padding: '7px 10px',
                      transition: 'background 0.12s',
                    }}
                      onMouseEnter={e => { e.currentTarget.style.background = '#f4f6fb' }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                    >
                      <span style={{ fontSize: 13, color: '#1a1a2e' }}>{p.nameKo || p.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 주요 사건 */}
          {node.topEvents?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <SectionHeader label="주요 사건" color={TYPE_COLOR.Event} count={node.topEvents.length} sectionKey="book-events" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-events'] === false && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingBottom: 4 }}>
                  {node.topEvents.map(e => (
                    <button key={e.id} onClick={() => onSelectNode(e.id)} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      width: '100%', textAlign: 'left', font: 'inherit',
                      border: 'none', background: 'none', cursor: 'pointer',
                      borderLeft: `3px solid ${TYPE_COLOR.Event}`,
                      borderRadius: 6, padding: '7px 10px',
                      transition: 'background 0.12s',
                    }}
                      onMouseEnter={ev => { ev.currentTarget.style.background = '#f4f6fb' }}
                      onMouseLeave={ev => { ev.currentTarget.style.background = 'none' }}
                    >
                      <span style={{ flex: 1, fontSize: 13, color: '#1a1a2e' }}>{e.nameKo || e.name}</span>
                      {e.startDate && (
                        <span style={{ fontSize: 10, color: '#9aa5b8', flexShrink: 0 }}>
                          {parseYear(e.startDate)}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Place 전용 블록 — 이웃 그룹보다 위. Book의 시대적 배경·대표 구절 미러. */}
      {node.label === 'Place' && (
        node.properties.background || node.properties.keyVerse ||
        groups['Event']?.length > 0 || (placePersons && placePersons.length > 0)
      ) && (
        <div style={{ padding: '12px 16px 4px', fontSize: 14 }}>
          {/* 장소 배경 */}
          {node.properties.background && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="장소 배경" color={TYPE_COLOR.Place} sectionKey="place-background" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-background'] === false && (
                <p style={{ margin: '0 0 4px', color: '#374151', lineHeight: 1.6 }}>{node.properties.background}</p>
              )}
            </div>
          )}

          {/* 대표 구절 */}
          {node.properties.keyVerse && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="대표 구절" color={TYPE_COLOR.Place} sectionKey="place-keyverse" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-keyverse'] === false && (
                <div style={{
                  padding: '10px 12px', background: '#f5f3ff', borderRadius: 8,
                  borderLeft: `3px solid ${TYPE_COLOR.Place}`, marginBottom: 4,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: placeKeyVerseText ? 4 : 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#6d28d9' }}>
                      {node.properties.keyVerse}
                    </div>
                    <span style={{ marginLeft: 'auto' }}>
                      <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color={TYPE_COLOR.Place} />
                    </span>
                  </div>
                  {placeKeyVerseText && (
                    <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{placeKeyVerseText}</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 이 장소의 사건 */}
          {groups['Event']?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="이 장소의 사건" color={TYPE_COLOR.Event} count={groups['Event'].length} sectionKey="place-events" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-events'] === false && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {groups['Event'].map(ev => (
                    <div key={ev.id}>
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '6px 8px', borderRadius: 6,
                        borderLeft: `3px solid ${TYPE_COLOR.Event}`,
                      }}>
                        <span style={{ flex: 1, fontSize: 13, color: '#1a1a2e' }}>{ev.nameKoMissing ? `${ev.name} (미번역)` : ev.nameKo}</span>
                        {renderPlaceBookChip(ev.id)}
                      </div>
                      {renderPlaceVerseView(ev.id)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 이 곳을 지난 다른 인물 */}
          {placePersons && placePersons.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="이 곳을 지난 인물" color={TYPE_COLOR.Person} count={placePersons.length} sectionKey="place-persons" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-persons'] === false && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, paddingBottom: 4 }}>
                  {placePersons.map(p => (
                    <button
                      key={p.id}
                      onClick={() => onExplorePerson(p.id)}
                      style={{
                        fontSize: 12, padding: '5px 12px', borderRadius: 999,
                        border: `1px solid ${TYPE_COLOR.Person}`,
                        background: 'rgba(74,144,217,0.08)', color: TYPE_COLOR.Person,
                        cursor: 'pointer', fontWeight: 600,
                      }}
                    >{p.nameKo}</button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 이웃 그룹 (Book 제외) */}
      {node.label !== 'Book' && (
      <div style={{ padding: '4px 12px 20px' }}>
        {node.neighbors.length === 0 && (
          <p style={{ color: '#7c8db0', fontSize: 13, padding: '12px 4px' }}>연결된 이웃이 없습니다</p>
        )}
        {TYPE_ORDER.filter(t => groups[t]?.length).map(t => (
          <div key={t} style={{ marginTop: 14 }}>
            <SectionHeader label={TYPE_KO[t] || t} color={TYPE_COLOR[t] || TYPE_COLOR.Unknown} count={groups[t].length} sectionKey={t} collapsed={collapsed} onToggle={toggle} />
            {collapsed[t] === false && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {groups[t].map(n => (
                  <button
                    key={n.id + ':' + n.relation}
                    onClick={() => onSelectNode(n.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      width: '100%', textAlign: 'left', font: 'inherit',
                      border: 'none', background: 'none', cursor: 'pointer',
                      borderLeft: `3px solid ${TYPE_COLOR[t]}`,
                      borderRadius: 6, padding: '8px 10px',
                      transition: 'background 0.12s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = '#f4f6fb' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                  >
                    <span style={{ flex: 1, fontSize: 14, color: '#1a1a2e' }}>
                      {n.nameKoMissing ? `${n.name} (미번역)` : n.nameKo}
                    </span>
                    <span style={{
                      fontSize: 10, color: '#7c8db0', background: '#eef0f5',
                      borderRadius: 4, padding: '2px 6px', flexShrink: 0,
                    }}>{REL_KO[n.relation] || n.relation}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {node.neighborTotal > node.neighbors.length && (
          <p style={{
            color: '#aab2c5', fontSize: 12, padding: '12px 6px 0',
            borderTop: '1px solid #eef0f5', marginTop: 14,
          }}>
            이웃 {node.neighborTotal}개 중 {node.neighbors.length}개 표시
          </p>
        )}
      </div>
      )}
    </div>
  )
}

export default SidePanel
