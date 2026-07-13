// 사이드 사건 리스트 — 여정 stops를 시간순으로 표시. props: stops(배열),
// activeStopIdx(number|null), onStopSelect(idx => void), verseLang/setVerseLang(구절 모달용).
// 좌표 있는 정차의 행 클릭은 지도 선택(onStopSelect)만 하고, activeStopIdx(deduped 인덱스)는
// 금색 하이라이트·자동 스크롤에 쓴다.
//
// 구절은 📖 칩 클릭 시 양피지 포털 모달(renderVerseLayer)로 연다 — 데스크톱·모바일 동일,
// 앱 전역 구절 열람(타임라인·관계·소개…)과 통일한 단일 패턴. 지도 위치 없는 정차는 행 전체 클릭으로
// 같은 모달을 연다(지도 선택 불가라).
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { MapPinOff } from 'lucide-react'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'
import { TYPE_COLOR } from './theme'

export default function JourneyList({ stops, activeStopIdx, onStopSelect, verseLang, setVerseLang, personName, tourName }) {
  const listRef = useRef(null)
  const activeRef = useRef(null)
  // 리스트에서 직접 클릭해 선택한 경우 자동 스크롤 억제(이미 보고 있는 행이 동일장소의 다른 행으로 점프하지 않게)
  const suppressScrollRef = useRef(false)
  // 구절 레이어(양피지 포털 모달) — 📖/장소없는 행 클릭으로 열림, 한 번에 하나. 앱 전역 구절 열람과 통일.
  const [verseView, setVerseView] = useState(null)      // { eventId, label, bookId } | null
  const [eventVerses, setEventVerses] = useState({ id: null, data: null })
  const openEventRef = useRef(null)

  // 지도 마커로 선택이 바뀐 경우에만 활성 정차지로 자동 스크롤(리스트 클릭은 억제)
  useEffect(() => {
    if (suppressScrollRef.current) {
      suppressScrollRef.current = false
      return
    }
    if (activeRef.current && listRef.current) {
      activeRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [activeStopIdx])

  if (!stops || stops.length === 0) return null

  // 구절 레이어 토글(양피지 모달). 열 때 /event/{id}/verses 1회 fetch(id로 묶어 stale 무시).
  const toggleVerseView = (stop) => {
    const evId = stop.eventId
    if (!evId) return
    if (verseView && verseView.eventId === evId) { setVerseView(null); openEventRef.current = null; return }
    openEventRef.current = evId
    setVerseView({ eventId: evId, label: stop.nameKo || stop.title, bookId: null })
    setEventVerses({ id: evId, data: null })
    apiGet('/event/' + evId + '/verses')
      .then(data => {
        if (openEventRef.current !== evId) return
        setVerseView(prev => prev && prev.eventId === evId ? { ...prev, bookId: (data.books || [])[0]?.bookId ?? null } : prev)
        setEventVerses({ id: evId, data })
      })
      .catch(e => { if (openEventRef.current === evId) { console.warn('[JourneyList] 사건 구절 로드 실패', e); setEventVerses({ id: evId, data: { books: [] } }) } })
  }
  const closeVerseView = () => { setVerseView(null); openEventRef.current = null }

  // 구절 레이어 — 스크롤/시트 래퍼 밖 body에 포털(오배치 함정 회피). 앱 전역 양피지 모달과 동일 UX.
  const renderVerseLayer = () => {
    if (!verseView) return null
    const evId = verseView.eventId
    const overlay = eventVerses.id === evId ? eventVerses.data : null
    const ovBooks = overlay ? (overlay.books || []) : []
    const selBook = ovBooks.find(b => b.bookId === verseView.bookId) || ovBooks[0]
    return createPortal(
      <div onClick={closeVerseView} style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
        <div onClick={e => e.stopPropagation()} style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontWeight: 700, fontSize: 15, flex: 1, fontFamily: 'var(--serif)' }}>{verseView.label}</span>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            <button onClick={closeVerseView} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
          </div>
          {ovBooks.length > 1 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
              {ovBooks.map(b => {
                const sel = b.bookId === selBook.bookId
                return (
                  <button key={b.bookId} onClick={() => setVerseView(prev => prev ? { ...prev, bookId: b.bookId } : prev)}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 11, padding: '1px 8px', borderRadius: 999, lineHeight: 1.7, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--paper-accent)', background: sel ? 'var(--paper-accent)' : 'transparent', color: sel ? 'var(--paper)' : 'var(--paper-accent)' }}
                  >{b.bookNameKo || b.bookId}</button>
                )
              })}
            </div>
          )}
          {overlay === null ? (
            <div style={{ padding: '12px 0' }}><Spinner size={20} color="var(--paper-accent)" /></div>
          ) : ovBooks.length === 0 ? (
            <div style={{ fontSize: 13, color: 'var(--paper-accent)', padding: '4px 0' }}>표시할 구절이 없습니다</div>
          ) : (
            <>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--paper-accent)', marginBottom: 8 }}>{selBook.bookNameKo || selBook.bookId} {selBook.rangeLabel}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {selBook.verses.map(v => {
                  const body = (verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'
                  return (
                    <div key={v.verseID} style={{ fontFamily: 'var(--serif)', fontSize: 15.5, lineHeight: 1.8, color: 'var(--paper-ink)' }}>
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
      document.body,
    )
  }

  // stops 중 좌표 있는 것을 deduplicate해 배지 seq → deduped 인덱스 매핑 구성
  // (MapView의 buildJourneyStopsGeoJSON과 동일 로직)
  const withCoord = stops.filter((s) => s.lng != null && s.lat != null)
  const coKey = (s) => `${s.lng},${s.lat}`
  const seen = []
  for (const s of withCoord) {
    const k = coKey(s)
    if (!seen.includes(k)) seen.push(k)
  }
  const keyToIdx = new Map(seen.map((k, i) => [k, i]))

  // 동일 좌표가 여러 사건에 걸칠 때, 활성 장소의 '첫' 정차지만 스크롤 타깃으로(마지막 행으로 점프 방지)
  const firstActiveRawIdx = activeStopIdx == null ? -1 : stops.findIndex((s) => {
    const kk = s.lng != null && s.lat != null ? coKey(s) : null
    return kk != null && keyToIdx.get(kk) === activeStopIdx
  })

  return (
    <div
      ref={listRef}
      style={{
        height: '100%',
        overflowY: 'auto',
        background: 'var(--bg-1)',
        borderRight: '1px solid var(--line)',
        WebkitTapHighlightColor: 'transparent',  // 📖 등 탭 시 기본 하이라이트(사각형) 깜빡임 제거 (RelationsView 패턴, 상속 속성)
      }}
    >
      {/* 헤더 — 여정 = 사건 묶음임을 명시(여정 > 사건 N개 > 각 사건의 구절) */}
      <div style={{ padding: '12px 14px 8px', borderBottom: '1px solid var(--line)' }}>
        <div style={{ color: 'var(--ink)', fontSize: 13, fontWeight: 700, fontFamily: 'var(--serif)' }}>
          {tourName || (personName ? `${personName}의 여정` : '여정')}
        </div>
        <div style={{ color: 'var(--ink-faint)', fontSize: 10, marginTop: 2 }}>
          사건 {stops.length}개 · 📖 눌러 구절 보기
        </div>
      </div>

      {stops.map((stop, rawIdx) => {
        const hasCoord = stop.lng != null && stop.lat != null
        const k = hasCoord ? coKey(stop) : null
        const dedupIdx = k != null ? keyToIdx.get(k) : null
        const isActive = dedupIdx != null && dedupIdx === activeStopIdx
        const expandable = stop.eventId != null
        const expanded = expandable && verseView?.eventId === stop.eventId
        // 사건(여정) 순번 — 지도 배지는 같은 장소의 순번들을 압축(예 "6-8, 10")으로 보여줘 일치
        const seq = stop.seq

        return (
          <div
            key={stop.eventId ?? rawIdx}
            ref={rawIdx === firstActiveRawIdx ? activeRef : null}
            style={{
              borderBottom: '1px solid var(--line)',
              background: isActive ? 'var(--bg-3)' : 'transparent',
              position: 'relative',
              transition: 'background 0.15s',
            }}
          >
            {/* 활성 행 — 왼쪽 금색 바(목업 .stop.on::before) */}
            {isActive && (
              <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: 'var(--gold)' }} />
            )}
            <div
              onClick={() => {
                if (hasCoord && dedupIdx != null) {
                  // 좌표 있는 정차 — 행 클릭 = 지도 선택만(구절은 📖로 연다).
                  if (dedupIdx !== activeStopIdx) suppressScrollRef.current = true  // 리스트 클릭 → 자동 스크롤 억제
                  onStopSelect(dedupIdx)
                } else if (expandable) {
                  // 지도 위치 없는 정차 — 지도 선택 불가라 행 전체가 구절 모달을 연다.
                  toggleVerseView(stop)
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                padding: '9px 14px',
                cursor: hasCoord || expandable ? 'pointer' : 'default',
              }}
            >
              {/* 순번 배지 — 목업 .stop .n(금 테두리 원, 활성 시 금 채움) */}
              {/* 순번 배지 — 좌표 있는 정차는 목업 .stop .n(금 테두리 원). 지도 위치 없는 정차는 순번 대신
                  MapPinOff 아이콘으로 "지도에 못 얹는 사건"임을 명시(흐림 대신 의도된 표식). */}
              <div style={{
                flexShrink: 0,
                width: 22, height: 22,
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 700,
                marginTop: 1,
                background: !hasCoord ? 'var(--bg-2)'
                  : isActive ? 'var(--gold)'
                  : 'var(--bg-0)',
                color: !hasCoord ? 'var(--ink-faint)' : isActive ? 'var(--bg-0)' : 'var(--gold)',
                border: !hasCoord ? '1px solid var(--line-strong)' : `1px solid ${isActive ? 'var(--gold)' : 'var(--gold-dim)'}`,
              }}>
                {hasCoord ? seq : <MapPinOff size={12} />}
              </div>

              {/* 사건명 + 장소명 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13,
                  color: isActive ? 'var(--gold)' : hasCoord ? 'var(--ink)' : 'var(--ink-dim)',
                  fontWeight: isActive ? 600 : 400,
                  lineHeight: 1.4,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {/* 테마 투어 — 여러 인물을 엮으므로 사건명 앞에 그 사건 주인공 라벨(백엔드 personNameKo). 인물 여정엔 없음. */}
                  {stop.personNameKo && (
                    <span style={{ color: TYPE_COLOR.Person, fontWeight: 600 }}>{stop.personNameKo} </span>
                  )}
                  {stop.nameKo || stop.title}
                </div>
                {stop.placeNameKo ? (
                  <div style={{
                    fontSize: 11,
                    color: 'var(--ink-faint)',
                    marginTop: 2,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {stop.placeNameKo}
                  </div>
                ) : !hasCoord ? (
                  // 지도 위치 없음 — 빈칸(흐림)이 아니라 이유를 명시. 실제 장소명과 구분되게 이탤릭.
                  <div style={{ fontSize: 11, color: 'var(--ink-faint)', marginTop: 2, fontStyle: 'italic' }}>
                    지도에 표시할 위치 없음
                  </div>
                ) : null}
              </div>

              {/* 펼침 토글 — 구절 있는 사건 행. 앱 전역 구절 칩 표준(Book 테두리·bg-2·"📖 구절")과 통일해
                  눈에 띄게 한다(사용자 피드백: 조용한 스타일이 안 보임 → M6의 필 제거를 되돌림). 펼침 시 반전. */}
              {expandable && (
                <span
                  onClick={(e) => {
                    e.stopPropagation()  // 행 onClick(지도 선택) 억제
                    // 펼칠 때(닫힘→열림)만 지도 동기화. 리스트 클릭이므로 자동 스크롤 억제.
                    if (!expanded && hasCoord && dedupIdx != null) {
                      if (dedupIdx !== activeStopIdx) suppressScrollRef.current = true
                      onStopSelect(dedupIdx)
                    }
                    toggleVerseView(stop)  // 양피지 모달 토글
                  }}
                  style={{
                  flexShrink: 0,
                  display: 'inline-flex', alignItems: 'center', gap: 3,
                  fontSize: 10, fontWeight: 700,
                  padding: '5px 10px', borderRadius: 999, lineHeight: 1.4,
                  margin: '-3px -2px -3px 0',  // 탭 히트영역 여유 — 행 높이 영향 최소화
                  cursor: 'pointer',
                  border: `1px solid ${TYPE_COLOR.Book}`,
                  background: expanded ? TYPE_COLOR.Book : 'var(--bg-2)',
                  color: expanded ? 'var(--bg-0)' : TYPE_COLOR.Book,
                }}>📖 구절 {expanded ? '▾' : '▸'}</span>
              )}
            </div>
          </div>
        )
      })}

      {renderVerseLayer()}
    </div>
  )
}
