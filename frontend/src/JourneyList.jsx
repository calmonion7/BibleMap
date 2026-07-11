// 사이드 사건 리스트 — 여정 stops를 시간순으로 "여정 > 사건 > 구절" 아코디언 트리로 표시.
// props: stops(배열), activeStopIdx(number|null), onStopSelect(idx => void),
//        verseLang/setVerseLang(사건 근거구절 표시용)
// 구절은 📖 칩 클릭으로만 토글하며 한 번에 하나만 열린다(expandedId). 사건 행 클릭은
// 지도 선택(onStopSelect)만 하고 열린 구절은 닫는다. activeStopIdx(지도 활성·deduped 인덱스)는
// 주황 하이라이트·자동 스크롤에 쓴다.
//
// onReadingChange가 주어지면(모바일) "읽기 모드": 펼침 상태를 상위(App)가 소유(readingEventId)하고,
// 📖 탭 시 리스트 대신 그 사건 구절만 EventVerses 읽기 레이아웃으로 단독 표시한다. 없으면(데스크톱)
// 기존 인라인 아코디언(expandedId 내부 상태)을 쓴다.
import { useEffect, useRef, useState } from 'react'
import EventVerses from './EventVerses'
import { TYPE_COLOR } from './theme'

export default function JourneyList({ stops, activeStopIdx, onStopSelect, verseLang, setVerseLang, personName, tourName, readingEventId, onReadingChange, onPersonIntro }) {
  const listRef = useRef(null)
  const activeRef = useRef(null)
  // 리스트에서 직접 클릭해 선택한 경우 자동 스크롤 억제(이미 보고 있는 행이 동일장소의 다른 행으로 점프하지 않게)
  const suppressScrollRef = useRef(false)
  // 펼친 사건(eventId) — 📖 칩으로만 토글, 한 번에 하나만 열림.
  const [expandedId, setExpandedId] = useState(null)

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

  // 읽기 모드(모바일): 상위가 소유한 readingEventId가 있으면 리스트 대신 그 사건 구절만 단독 표시.
  const controlled = onReadingChange != null
  if (controlled && readingEventId) {
    const ev = stops.find((s) => s.eventId === readingEventId)
    return (
      <div style={{ height: '100%', background: 'var(--bg-1)' }}>
        <EventVerses
          eventId={readingEventId}
          heading={ev?.nameKo || ev?.title || '구절'}
          onClose={() => onReadingChange(null)}
          verseLang={verseLang}
          setVerseLang={setVerseLang}
        />
      </div>
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
        const openId = controlled ? readingEventId : expandedId
        const expanded = expandable && openId === stop.eventId
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
                // 행 클릭 = 지도 선택만. 열린 구절은 닫는다(구절은 📖로만 토글).
                if (hasCoord && dedupIdx != null) {
                  if (dedupIdx !== activeStopIdx) suppressScrollRef.current = true  // 리스트 클릭 → 자동 스크롤 억제
                  onStopSelect(dedupIdx)
                }
                if (!controlled) setExpandedId(null)
              }}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                padding: '9px 14px',
                cursor: hasCoord ? 'pointer' : 'default',
                opacity: hasCoord ? 1 : 0.55,
              }}
            >
              {/* 순번 배지 — 목업 .stop .n(금 테두리 원, 활성 시 금 채움) */}
              <div style={{
                flexShrink: 0,
                width: 22, height: 22,
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 700,
                marginTop: 1,
                background: seq == null ? 'var(--bg-2)'
                  : isActive ? 'var(--gold)'
                  : 'var(--bg-0)',
                color: seq == null ? 'var(--ink-faint)' : isActive ? 'var(--bg-0)' : 'var(--gold)',
                border: seq == null ? '1px solid transparent' : `1px solid ${isActive ? 'var(--gold)' : 'var(--gold-dim)'}`,
              }}>
                {seq != null ? seq : '·'}
              </div>

              {/* 사건명 + 장소명 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13,
                  color: isActive ? 'var(--gold)' : hasCoord ? 'var(--ink)' : 'var(--ink-faint)',
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
                {stop.placeNameKo && (
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
                )}
              </div>

              {/* 펼침 토글 — 구절 있는 사건 행. 감사 M6: 필 배경 제거, 조용한 아이콘/텍스트(호버·활성 시 금색). */}
              {expandable && (
                <span
                  onClick={(e) => {
                    e.stopPropagation()  // 행 onClick(지도 선택·닫기) 억제
                    const willOpen = !expanded  // 단일 오픈 토글
                    if (controlled) onReadingChange(willOpen ? stop.eventId : null)  // 모바일: 읽기 모드(상위 소유)
                    else setExpandedId(willOpen ? stop.eventId : null)               // 데스크톱: 인라인 아코디언
                    // 펼칠 때만 지도 동기화(접을 때 카메라 이동 방지). 리스트 클릭이므로 자동 스크롤 억제.
                    if (willOpen && hasCoord && dedupIdx != null) {
                      if (dedupIdx !== activeStopIdx) suppressScrollRef.current = true
                      onStopSelect(dedupIdx)
                    }
                  }}
                  onMouseEnter={(e) => { if (!expanded) e.currentTarget.style.color = 'var(--gold)' }}
                  onMouseLeave={(e) => { if (!expanded) e.currentTarget.style.color = 'var(--ink-faint)' }}
                  style={{
                  flexShrink: 0,
                  display: 'inline-flex', alignItems: 'center', gap: 3,
                  fontSize: 10, fontWeight: 700,
                  padding: '8px 11px', borderRadius: 999, lineHeight: 1.4,
                  margin: '-6px -4px -6px 0',  // 탭 히트영역 확대(모바일 오조작 방지) — 행 높이 영향 최소화
                  cursor: 'pointer',
                  border: '1px solid transparent',
                  background: 'none',
                  color: expanded ? 'var(--gold)' : 'var(--ink-faint)',
                }}>📖 {expanded ? '▾' : '▸'}</span>
              )}
            </div>

            {/* 펼친 사건의 근거구절 — 데스크톱만 인라인 표시. 모바일(controlled)은 읽기 모드(상단 분기)로 처리. */}
            {expanded && !controlled && (
              <div onClick={(e) => e.stopPropagation()} style={{ padding: '0 12px 10px 30px' }}>
                <EventVerses eventId={stop.eventId} verseLang={verseLang} setVerseLang={setVerseLang} />
              </div>
            )}
          </div>
        )
      })}

      {/* 여정 마지막 페이지 — 인물 소개(성품·연결 상세 레이어). 인물 모드 전용(투어는 단일 주인공 없음). */}
      {personName && onPersonIntro && (
        <div
          onClick={onPersonIntro}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-2)' }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'none' }}
          style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', cursor: 'pointer', borderTop: '1px solid var(--line)', transition: 'background 0.12s' }}
        >
          <div style={{
            flexShrink: 0, width: 22, height: 22, borderRadius: '50%',
            display: 'grid', placeItems: 'center', fontSize: 11,
            color: 'var(--gold)', border: '1px solid var(--gold-dim)', background: 'var(--bg-0)',
          }}>✦</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gold)', fontFamily: 'var(--serif)' }}>{personName} 인물 소개</div>
            <div style={{ fontSize: 11, color: 'var(--ink-faint)', marginTop: 2 }}>성품 · 함께 등장한 인물 · 연결</div>
          </div>
          <span style={{ color: 'var(--ink-faint)', fontSize: 12, flexShrink: 0 }}>▸</span>
        </div>
      )}
    </div>
  )
}
