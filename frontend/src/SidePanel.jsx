import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { TYPE_COLOR, TYPE_KO, NIGHT, GENRE_META } from './theme'
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

// 구조 개요 프로즈 → 타임라인 세그먼트 배열. ' · '로 세그먼트 분할, 각 세그먼트 끝의
// 마지막 괄호 (...)를 범위 배지로·앞 텍스트를 라벨로. 끝 괄호가 없으면 라벨만(range null).
// 절 범위(1~25절)·범위 없는 세그먼트(다양한 장르)·시편 중첩 등 예외를 견고하게 흡수한다.
function parseStructure(str) {
  return str.split(' · ').map(seg => {
    const s = seg.trim()
    const m = s.match(/^(.*)\(([^()]+)\)$/)
    return m ? { range: m[2].trim(), label: m[1].trim() } : { range: null, label: s }
  }).filter(seg => seg.label || seg.range)
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
        fontSize: 12, fontWeight: 700, color: 'var(--ink-dim)',
      }}
    >
      {/* 타입 점 색은 theme.js typeColor 그대로(호출부에서 넘긴 color) — 라벨 텍스트는 ink-dim으로 분리 */}
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <span style={{ flex: 1, textAlign: 'left' }}>{label}</span>
      {count != null && <span style={{ color: 'var(--ink-faint)', fontWeight: 500 }}>{count}</span>}
      <span style={{ fontSize: 10, color: 'var(--ink-faint)', marginLeft: 2 }}>{isOpen ? '▾' : '▸'}</span>
    </button>
  )
}

function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false, onNodeLoaded, verseLang, setVerseLang, explorePersonId = null, onExplorePerson = () => {}, curatedIds = null, onExploreJourney = () => {}, onClose, stickyTop = 0 }) {
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

  // Person 블록 — 인물 연결(함께 등장한 인물·동시대 인물): { forNodeId, coParticipants, contemporaries } | null
  const [connectionsState, setConnectionsState] = useState(null)
  const connections = connectionsState?.forNodeId === nodeId ? connectionsState : null

  // 인물 성품 구절 레이어 — 인라인 아코디언 대신 양피지 포털 모달(사건 구절 레이어와 동일 패턴).
  // forNodeId 키로 인물 변경 시 자동 닫힘.
  const [traitLayerRaw, setTraitLayer] = useState(null)   // { forNodeId, idx } | null
  const traitLayerIdx = traitLayerRaw?.forNodeId === nodeId ? traitLayerRaw.idx : null

  useEffect(() => {
    if (!nodeId) return
    let cancelled = false
    apiGet('/node/' + nodeId)
      .then(data => { if (!cancelled) {
        // Book은 전 섹션 기본 펼침 — 탭 0회로 모든 정보 도달(접기 토글은 유지, 노드 왕복에도 항상 펼침)
        // Place는 서술 섹션(배경·대표 구절)만 기본 펼침 — 이웃 목록(사건·인물)은 접힘 유지(M3)
        setCollapsed(data.label === 'Book' ? {
          'book-central': false, 'book-themes': false, 'book-keyverse': false, 'book-background': false,
          'book-structure': false, 'book-keyppl': false, 'book-persons': false, 'book-events': false,
        } : data.label === 'Place' ? {
          'place-background': false, 'place-keyverse': false,
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
      .catch(e => { if (!cancelled) { console.warn('[SidePanel] 장소 경유 인물 로드 실패', e); setPlacePersonsState({ forNodeId: nodeId, persons: [] }) } })
    return () => { cancelled = true }
  }, [nodeId, state.id, state.node, explorePersonId])

  // Person 블록 — 인물 연결 fetch (큐레이션 인물만)
  useEffect(() => {
    if (!nodeId) return
    const node = state.id === nodeId ? state.node : null
    if (!node || node.label !== 'Person' || !curatedIds?.has(node.id)) return
    let cancelled = false
    apiGet(`/person/${nodeId}/connections`)
      .then(data => { if (!cancelled) setConnectionsState({ forNodeId: nodeId, coParticipants: data.coParticipants ?? [], contemporaries: data.contemporaries ?? [] }) })
      .catch(e => { if (!cancelled) { console.warn('[SidePanel] 인물 연결 로드 실패', e); setConnectionsState({ forNodeId: nodeId, coParticipants: [], contemporaries: [] }) } })
    return () => { cancelled = true }
  }, [nodeId, state.id, state.node, curatedIds])

  const ready = state.id === nodeId
  const node = ready ? state.node : null
  const error = ready ? state.error : null

  const msgStyle = { padding: '1.25rem', fontSize: 14, color: 'var(--ink-faint)' }
  if (!nodeId) return <p style={msgStyle}>지도에서 마커를 클릭하세요</p>
  // Spinner는 color+'22'로 알파를 이어붙여 border를 만들어 var()나 rgba(원래 rgba(100,120,180,0.6)도 동일 결함)를 못 받는다
  // (JS 계산 지점) — theme.js NIGHT의 순수 hex 리터럴만 사용
  if (!ready) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}><Spinner color={NIGHT.gold} /></div>
  // 에러 색 '#dc3545' — Night Atlas 토큰 미정의, 유지
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
  // 주요 인물 = 이벤트 참여 Person(topPersons; 큐레이션은 발자취 링크) + 책 keyPeople 문자열(링크 없는 평문) 병합.
  // 나오미·보아스처럼 그래프 Person 노드가 아닌 인물은 keyPeople에만 있으므로 이렇게 합쳐야 노출된다. 이름 중복 제거.
  const eventPersons = node.label === 'Book' ? (node.topPersons || []) : []
  const eventPersonNames = new Set(eventPersons.map(p => p.nameKo || p.name))
  const keyOnlyPersons = node.label === 'Book'
    ? (node.properties.keyPeople || []).filter(name => !eventPersonNames.has(name))
    : []

  function toggle(key) {
    setCollapsed(prev => ({ ...prev, [key]: prev[key] === false }))
  }

  // Place 블록 — 사건 근거구절 드릴다운 헬퍼 (TimelineView 패턴 이식). 다크 시트 위 참조 칩(근거에만 남긴 칩, 원칙 5)
  const placeChipBase = {
    display: 'inline-flex', alignItems: 'center', gap: 3,
    fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
    border: `1px solid ${TYPE_COLOR.Book}`, cursor: 'pointer', fontWeight: 600,
    background: 'var(--bg-2)', color: TYPE_COLOR.Book,
  }
  // 양피지 구절 카드 — 절 본문 전용(원칙 2). 인용문(설명 산문)이 아닌 실제 성경 본문에만 사용.
  const paperCardStyle = {
    margin: '4px 0 6px', padding: '10px 12px',
    background: 'var(--paper)', borderRadius: 'var(--r-m)', boxShadow: 'var(--shadow-1)',
  }
  const paperTextStyle = { fontFamily: 'var(--serif)', fontSize: 15.5, lineHeight: 1.8, color: 'var(--paper-ink)' }

  // 인물 연결 칩 — '이 곳을 지난 인물' 칩과 동일 스타일. 근거 칩이 아니므로 중립 톤(원칙 5).
  const CONN_CHIP = {
    fontSize: 12, padding: '5px 12px', borderRadius: 999,
    border: '1px solid var(--line-strong)',
    background: 'var(--bg-2)', color: 'var(--ink-dim)',
    cursor: 'pointer', fontWeight: 600,
  }

  function togglePlaceVerseView(evId, label) {
    if (placeVerseView && placeVerseView.eventId === evId) {
      setPlaceVerseView(null); placeOpenEventRef.current = null; return
    }
    placeOpenEventRef.current = evId
    setPlaceVerseView({ forNodeId: nodeId, eventId: evId, label, bookId: null })
    setPlaceEventVerses({ id: evId, data: null })
    apiGet('/event/' + evId + '/verses')
      .then(data => {
        if (placeOpenEventRef.current !== evId) return
        // 첫 번째 권을 기본 선택
        const firstBookId = (data.books || [])[0]?.bookId ?? null
        setPlaceVerseView(prev => prev && prev.eventId === evId ? { ...prev, bookId: firstBookId } : prev)
        setPlaceEventVerses({ id: evId, data })
      })
      .catch(e => { if (placeOpenEventRef.current === evId) { console.warn('[SidePanel] 사건 구절 로드 실패', e); setPlaceEventVerses({ id: evId, data: { books: [] } }) } })
  }

  function renderPlaceBookChip(evId, label) {
    const open = placeVerseView != null && placeVerseView.eventId === evId
    return (
      <button
        onClick={(e) => { e.stopPropagation(); togglePlaceVerseView(evId, label) }}
        style={{ ...placeChipBase, marginLeft: 6, ...(open ? { background: TYPE_COLOR.Book, color: 'var(--bg-0)' } : null) }}
      >📖 구절 ▸</button>
    )
  }

  // 구절 레이어 — 시트는 스크롤+transform 래퍼 안이라(absolute/fixed 오배치 함정) 포털로 body에 띄운다.
  // 타임라인·관계 뷰의 양피지 모달과 동일 UX(원스텝: 열자마자 절 본문).
  const closePlaceVerseView = () => { setPlaceVerseView(null); placeOpenEventRef.current = null }

  function renderVerseLayer() {
    if (!placeVerseView) return null
    const evId = placeVerseView.eventId
    const overlay = placeEventVerses.id === evId ? placeEventVerses.data : null
    const ovBooks = overlay ? (overlay.books || []) : []
    const selBook = ovBooks.find(b => b.bookId === placeVerseView.bookId) || ovBooks[0]
    return createPortal(
      <div
        onClick={closePlaceVerseView}
        // 모달 스크림 — 전용 토큰 없어 값 유지(다크 배경 위 반투명 오버레이라 무해)
        style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
      >
        {/* 근거 구절 모달 = 양피지 카드(원칙 2) */}
        <div onClick={e => e.stopPropagation()} style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontWeight: 700, fontSize: 15, flex: 1, fontFamily: 'var(--serif)' }}>{placeVerseView.label}</span>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            <button onClick={closePlaceVerseView} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
          </div>
          {ovBooks.length > 1 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
              {ovBooks.map(b => {
                const sel = b.bookId === selBook.bookId
                return (
                  <button
                    key={b.bookId}
                    onClick={() => setPlaceVerseView(prev => prev ? { ...prev, bookId: b.bookId } : prev)}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 3,
                      fontSize: 11, padding: '1px 8px', borderRadius: 999, lineHeight: 1.7, fontWeight: 600, cursor: 'pointer',
                      border: '1px solid var(--paper-accent)',
                      background: sel ? 'var(--paper-accent)' : 'transparent',
                      color: sel ? 'var(--paper)' : 'var(--paper-accent)',
                    }}
                  >{b.bookNameKo || b.bookId}</button>
                )
              })}
            </div>
          )}
          {overlay === null ? (
            <div style={{ padding: '12px 0' }}><Spinner size={20} color={NIGHT.paperAccent} /></div>
          ) : ovBooks.length === 0 ? (
            <div style={{ fontSize: 13, color: 'var(--paper-accent)', padding: '4px 0' }}>표시할 구절이 없습니다</div>
          ) : (
            <>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--paper-accent)', marginBottom: 8 }}>
                {selBook.bookNameKo || selBook.bookId} {selBook.rangeLabel}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {selBook.verses.map(v => {
                  const body = (verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'
                  return (
                    <div key={v.verseID} style={paperTextStyle}>
                      <span style={{ fontWeight: 700, color: 'var(--paper-accent)', marginRight: 6 }}>{v.chapter}:{v.verse}</span>
                      {body}
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>,
      document.body
    )
  }

  // 인물 성품 구절 레이어 — 사건 구절 레이어와 동일한 양피지 포털 모달.
  function renderTraitLayer() {
    if (traitLayerIdx == null) return null
    const t = node?.properties?.traits?.[traitLayerIdx]
    if (!t) return null
    const verseText = verseLang === 'ko' ? t.verse_textKo : t.verse_textEn
    return createPortal(
      <div
        onClick={() => setTraitLayer(null)}
        style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
      >
        <div onClick={e => e.stopPropagation()} style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontWeight: 700, fontSize: 15, flex: 1, fontFamily: 'var(--serif)' }}>{t.trait}</span>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            <button onClick={() => setTraitLayer(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--paper-accent)', marginBottom: 8 }}>{t.verse_ref}</div>
          {verseText
            ? <div style={paperTextStyle}>{verseText}</div>
            : <div style={{ fontSize: 13, color: 'var(--paper-accent)' }}>원문이 없습니다</div>}
        </div>
      </div>,
      document.body
    )
  }

  return (
    <div style={{ fontFamily: 'var(--sans)' }}>
      {renderVerseLayer()}
      {renderTraitLayer()}
      {/* 헤더 — 표면 var(--bg-1), 경계 var(--line), 제목 var(--serif)(h2 전역 규칙 상속) */}
      <div style={{
        padding: '14px 44px 14px 16px',
        borderBottom: '1px solid var(--line)',
        position: 'sticky', top: stickyTop, background: 'var(--bg-1)', zIndex: 1,
      }}>
        {onClose && (
          <button
            onClick={onClose}
            aria-label="닫기"
            style={{
              position: 'absolute', top: 10, right: 10, zIndex: 2,
              width: 40, height: 40, borderRadius: '50%',
              border: '1px solid var(--line-strong)', background: 'var(--bg-2)', color: 'var(--ink-dim)',
              cursor: 'pointer', fontSize: 20, lineHeight: 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >×</button>
        )}
        {canGoBack && (
          <button
            onClick={onBack}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              border: 'none', background: 'none', cursor: 'pointer',
              color: 'var(--ink-faint)', fontSize: 13, padding: 0, marginBottom: 8, font: 'inherit',
            }}
          >← 뒤로</button>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: headColor, flexShrink: 0 }} />
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: 'var(--ink)', lineHeight: 1.3 }}>{title}</h2>
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginTop: 3, marginLeft: 18 }}>{subtitle}</div>
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
              fontSize: 13, fontWeight: 700, color: 'var(--ink)',
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
          background: 'var(--bg-2)', border: '1px solid var(--line)',
        }}>
          {/* 한/영 탭은 구절 레이어 안에 있으므로 섹션 헤더에선 제거(중복) */}
          <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Person, marginBottom: 10 }}>인물 성품</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {node.properties.traits.map((t, i) => (
              <div key={i}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600, color: 'var(--ink)',
                    background: 'var(--bg-3)', borderRadius: 4, padding: '2px 8px',
                  }}>{t.trait}</span>
                  {/* 구절 참조 칩 → 양피지 레이어(다른 곳과 동일 패턴). 인라인 펼침 아님. */}
                  <button
                    onClick={() => setTraitLayer({ forNodeId: nodeId, idx: i })}
                    style={{ ...placeChipBase, borderColor: 'var(--line-strong)' }}
                  >📖 {t.verse_ref}</button>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{t.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Person 인물 연결 — 함께 등장한 인물 · 동시대 인물 (큐레이션 한정, 인물 성품 아래·이웃 그룹 위) */}
      {node.label === 'Person' && curatedIds?.has(node.id) && connections &&
        (connections.coParticipants.length > 0 || connections.contemporaries.length > 0) && (
        <div style={{ padding: '4px 16px 0', fontSize: 14 }}>
          {connections.coParticipants.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <SectionHeader label="함께 등장한 인물" color={TYPE_COLOR.Person} count={connections.coParticipants.length} sectionKey="conn-co" collapsed={collapsed} onToggle={toggle} />
              {collapsed['conn-co'] === false && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, paddingBottom: 4 }}>
                  {connections.coParticipants.map(p => (
                    <button key={p.id} onClick={() => onExploreJourney(p.id)} style={CONN_CHIP}>{p.nameKo}</button>
                  ))}
                </div>
              )}
            </div>
          )}
          {connections.contemporaries.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <SectionHeader label="동시대 인물" color={TYPE_COLOR.Person} count={connections.contemporaries.length} sectionKey="conn-contemp" collapsed={collapsed} onToggle={toggle} />
              {collapsed['conn-contemp'] === false && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, paddingBottom: 4 }}>
                  {connections.contemporaries.map(p => (
                    <button key={p.id} onClick={() => onExploreJourney(p.id)} style={CONN_CHIP}>{p.nameKo}</button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Book 전용 뷰 */}
      {node.label === 'Book' && (
        <div style={{ padding: '12px 16px 20px', fontSize: 14 }}>
          {/* 메타 칩 */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
            {/* 장르는 한글(GENRE_META), 사건 파생 연도범위(startYear~endYear)는 오해 유발(인용 오염 가능·저작 칩과 중복)이라 제외 */}
            {[node.properties.testament,
              node.properties.genre && (GENRE_META[node.properties.genre]?.displayName || node.properties.genre),
              node.properties.chapterCount && `${node.properties.chapterCount}장`,
              node.properties.verseCount && `${node.properties.verseCount}절`,
              node.properties.authorKo && node.properties.writtenDate && `${node.properties.authorKo} · ${node.properties.writtenDate}`]
              .filter(Boolean).map((chip, i) => (
              <span key={i} style={{
                fontSize: 11, padding: '3px 8px', borderRadius: 999,
                border: '1px solid var(--line-strong)', background: 'var(--bg-2)', color: 'var(--ink-dim)',
              }}>{chip}</span>
            ))}
          </div>

          {/* 중심 메시지 — 책의 정수(1~2줄)를 최상단에. 인용문 아닌 서술이라 다크 카드(양피지 아님) */}
          {node.properties.centralMessage && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="중심 메시지" color={TYPE_COLOR.Book} sectionKey="book-central" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-central'] === false && (
                <div style={{
                  padding: '10px 12px', background: 'var(--bg-2)', borderRadius: 8,
                  borderLeft: `3px solid ${TYPE_COLOR.Book}`, marginBottom: 4,
                  fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.6,
                }}>{node.properties.centralMessage}</div>
              )}
            </div>
          )}

          {/* 성경 주제 */}
          {node.properties.themes?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="핵심 주제" color={TYPE_COLOR.Book} sectionKey="book-themes" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-themes'] === false && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', paddingBottom: 4 }}>
                  {node.properties.themes.map((t, i) => (
                    <span key={i} style={{
                      fontSize: 12, padding: '4px 10px', borderRadius: 999,
                      border: '1px solid var(--line-strong)', background: 'var(--bg-2)', color: 'var(--ink-dim)',
                    }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 대표 구절 — 양피지 카드(원칙 2, 실제 성경 본문) */}
          {node.properties.keyVerse && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="대표 구절" color={TYPE_COLOR.Book} sectionKey="book-keyverse" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-keyverse'] === false && (
                <div style={paperCardStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: keyVerseText ? 6 : 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--paper-accent)' }}>
                      {node.properties.keyVerse}
                    </div>
                    <span style={{ marginLeft: 'auto' }}>
                      <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color="var(--paper-accent)" />
                    </span>
                  </div>
                  {keyVerseText && (
                    <div style={paperTextStyle}>{keyVerseText}</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 시대적 배경 — 긴 산문은 정수 아래로. 인용문 아닌 서술이라 다크 톤(양피지 아님) */}
          {node.properties.background && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="시대적 배경" color={TYPE_COLOR.Book} sectionKey="book-background" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-background'] === false && (
                <p style={{ margin: '0 0 4px', color: 'var(--ink-dim)', lineHeight: 1.6 }}>{node.properties.background}</p>
              )}
            </div>
          )}

          {/* 구조 개요 */}
          {node.properties.structure && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="구조 개요" color={TYPE_COLOR.Book} sectionKey="book-structure" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-structure'] === false && (
                // 세로 타임라인 — 좌측 스파인(점+연결선) + 장범위 배지(placeChipBase) + 라벨. 책 전개를 위→아래로.
                <div style={{ margin: '2px 0 4px' }}>
                  {parseStructure(node.properties.structure).map((seg, i, arr) => {
                    const last = i === arr.length - 1
                    return (
                      <div key={i} style={{ display: 'flex', gap: 10 }}>
                        <div style={{ flexShrink: 0, width: 10, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <span style={{ width: 9, height: 9, borderRadius: '50%', background: TYPE_COLOR.Book, marginTop: 5, flexShrink: 0 }} />
                          {!last && <span style={{ flex: 1, width: 2, background: 'var(--line-strong)', marginTop: 2 }} />}
                        </div>
                        <div style={{ flex: 1, minWidth: 0, paddingBottom: last ? 0 : 12, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          {seg.range && <span style={{ ...placeChipBase, flexShrink: 0 }}>{seg.range}</span>}
                          <span style={{ fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{seg.label}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* 주요 인물 — 이벤트 참여 인물 + 책 keyPeople 병합 전원 표시. 발자취(여정) 있는 큐레이션 인물만 클릭 가능
              (👣 발자취 칩 → 인물맵). 발자취 없는 인물(나오미·보아스 등 keyPeople 전용)은 이름만, 링크 없음. */}
          {(eventPersons.length + keyOnlyPersons.length) > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="주요 인물" color={TYPE_COLOR.Person} count={eventPersons.length + keyOnlyPersons.length} sectionKey="book-persons" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-persons'] === false && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingBottom: 4 }}>
                  {eventPersons.map(p => {
                    const curated = curatedIds?.has(p.id)
                    const rowStyle = {
                      display: 'flex', alignItems: 'center', gap: 8,
                      width: '100%', textAlign: 'left', font: 'inherit',
                      border: 'none', background: 'none',
                      borderLeft: `3px solid ${TYPE_COLOR.Person}`,
                      borderRadius: 6, padding: '7px 10px',
                    }
                    return curated ? (
                      <button key={p.id} onClick={() => onExploreJourney(p.id)} style={{ ...rowStyle, cursor: 'pointer', transition: 'background 0.12s' }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-2)' }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                      >
                        <span style={{ flex: 1, fontSize: 13, color: 'var(--ink)' }}>{p.nameKo || p.name}</span>
                        <span style={{ ...placeChipBase, flexShrink: 0 }}>👣 발자취 ▸</span>
                      </button>
                    ) : (
                      <div key={p.id} style={rowStyle}>
                        <span style={{ flex: 1, fontSize: 13, color: 'var(--ink-dim)' }}>{p.nameKo || p.name}</span>
                      </div>
                    )
                  })}
                  {/* keyPeople 전용(그래프 Person 노드 아님) — 링크 없는 평문 행 */}
                  {keyOnlyPersons.map((name, i) => (
                    <div key={`kp-${i}`} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      borderLeft: `3px solid ${TYPE_COLOR.Person}`,
                      borderRadius: 6, padding: '7px 10px',
                    }}>
                      <span style={{ flex: 1, fontSize: 13, color: 'var(--ink-dim)' }}>{name}</span>
                    </div>
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
                  {/* 행은 div+onClick(중첩 button 회피) — 📖 구절 드릴은 Place 블록 헬퍼 재사용(사건 id 기준이라 공용) */}
                  {node.topEvents.map(e => (
                    <div key={e.id}>
                      <div onClick={() => onSelectNode(e.id)} style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        width: '100%', textAlign: 'left', font: 'inherit', boxSizing: 'border-box',
                        cursor: 'pointer',
                        borderLeft: `3px solid ${TYPE_COLOR.Event}`,
                        borderRadius: 6, padding: '7px 10px',
                        transition: 'background 0.12s',
                      }}
                        onMouseEnter={ev => { ev.currentTarget.style.background = 'var(--bg-2)' }}
                        onMouseLeave={ev => { ev.currentTarget.style.background = 'none' }}
                      >
                        <span style={{ flex: 1, fontSize: 13, color: 'var(--ink)' }}>{e.nameKo || e.name}</span>
                        {e.startDate && (
                          <span style={{ fontSize: 10, color: 'var(--ink-faint)', flexShrink: 0 }}>
                            {parseYear(e.startDate)}
                          </span>
                        )}
                        {renderPlaceBookChip(e.id, e.nameKo || e.name)}
                      </div>
                    </div>
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
          {/* 장소 배경 — 인용문 아닌 서술이라 다크 톤(양피지 아님) */}
          {node.properties.background && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="장소 배경" color={TYPE_COLOR.Place} sectionKey="place-background" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-background'] === false && (
                <p style={{ margin: '0 0 4px', color: 'var(--ink-dim)', lineHeight: 1.6 }}>{node.properties.background}</p>
              )}
            </div>
          )}

          {/* 대표 구절 — 양피지 카드(원칙 2, 실제 성경 본문) */}
          {node.properties.keyVerse && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="대표 구절" color={TYPE_COLOR.Place} sectionKey="place-keyverse" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-keyverse'] === false && (
                <div style={paperCardStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: placeKeyVerseText ? 6 : 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--paper-accent)' }}>
                      {node.properties.keyVerse}
                    </div>
                    <span style={{ marginLeft: 'auto' }}>
                      <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color="var(--paper-accent)" />
                    </span>
                  </div>
                  {placeKeyVerseText && (
                    <div style={paperTextStyle}>{placeKeyVerseText}</div>
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
                        <span style={{ flex: 1, fontSize: 13, color: 'var(--ink)' }}>{ev.nameKoMissing ? `${ev.name} (미번역)` : ev.nameKo}</span>
                        {renderPlaceBookChip(ev.id, ev.nameKoMissing ? ev.name : ev.nameKo)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 이 곳을 지난 다른 인물 — 근거 칩이 아니므로 중립 톤(원칙 5, CONN_CHIP과 동일) */}
          {placePersons && placePersons.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="이 곳을 지난 인물" color={TYPE_COLOR.Person} count={placePersons.length} sectionKey="place-persons" collapsed={collapsed} onToggle={toggle} />
              {collapsed['place-persons'] === false && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, paddingBottom: 4 }}>
                  {placePersons.map(p => (
                    <button key={p.id} onClick={() => onExplorePerson(p.id)} style={CONN_CHIP}>{p.nameKo}</button>
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
          <p style={{ color: 'var(--ink-faint)', fontSize: 13, padding: '12px 4px' }}>연결된 이웃이 없습니다</p>
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
                    onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-2)' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                  >
                    <span style={{ flex: 1, fontSize: 14, color: 'var(--ink)' }}>
                      {n.nameKoMissing ? `${n.name} (미번역)` : n.nameKo}
                    </span>
                    <span style={{
                      fontSize: 10, color: 'var(--ink-faint)', background: 'var(--bg-2)',
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
            color: 'var(--ink-faint)', fontSize: 12, padding: '12px 6px 0',
            borderTop: '1px solid var(--line)', marginTop: 14,
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
