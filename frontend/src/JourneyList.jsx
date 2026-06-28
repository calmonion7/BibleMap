// 사이드 사건 리스트 — 여정 stops를 시간순으로 "여정 > 사건 > 구절" 아코디언 트리로 표시.
// props: stops(배열), activeStopIdx(number|null), onStopSelect(idx => void),
//        verseLang/setVerseLang(사건 근거구절 표시용)
// 각 사건을 독립적으로 펼침(여러 개 동시 가능). activeStopIdx(지도 활성·deduped 인덱스)는
// 주황 하이라이트·자동 스크롤에만 쓰고, 구절 펼침은 expandedIds(사건별)로 분리한다.
import { useEffect, useRef, useState } from 'react'
import EventVerses from './EventVerses'

export default function JourneyList({ stops, activeStopIdx, onStopSelect, verseLang, setVerseLang }) {
  const listRef = useRef(null)
  const activeRef = useRef(null)
  // 펼친 사건 집합(eventId) — 행마다 독립 토글, 지도 선택과 무관.
  const [expandedIds, setExpandedIds] = useState(() => new Set())

  // 지도 활성 항목으로 자동 스크롤
  useEffect(() => {
    if (activeRef.current && listRef.current) {
      activeRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [activeStopIdx])

  if (!stops || stops.length === 0) return null

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

  const toggle = (eventId) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(eventId)) next.delete(eventId)
      else next.add(eventId)
      return next
    })
  }

  return (
    <div
      ref={listRef}
      style={{
        height: '100%',
        overflowY: 'auto',
        background: 'rgba(20, 22, 50, 0.97)',
        borderRight: '1px solid rgba(255,255,255,0.07)',
      }}
    >
      <div style={{ padding: '12px 14px 6px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, letterSpacing: 0.5 }}>여정 순서</span>
      </div>
      {stops.map((stop, rawIdx) => {
        const hasCoord = stop.lng != null && stop.lat != null
        const k = hasCoord ? coKey(stop) : null
        const dedupIdx = k != null ? keyToIdx.get(k) : null
        const isActive = dedupIdx != null && dedupIdx === activeStopIdx
        const expandable = stop.eventId != null
        const expanded = expandable && expandedIds.has(stop.eventId)
        // 사건(여정) 순번 — 지도 배지는 같은 장소의 순번들을 압축(예 "6-8, 10")으로 보여줘 일치
        const seq = stop.seq

        return (
          <div
            key={stop.eventId ?? rawIdx}
            ref={isActive ? activeRef : null}
            style={{
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              background: isActive ? 'rgba(124,156,252,0.15)' : 'transparent',
              transition: 'background 0.15s',
            }}
          >
            <div
              onClick={() => {
                if (!expandable) return
                const willExpand = !expandedIds.has(stop.eventId)
                toggle(stop.eventId)
                // 펼칠 때만 지도 동기화(접을 때 카메라 이동 방지)
                if (willExpand && hasCoord && dedupIdx != null) onStopSelect(dedupIdx)
              }}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                padding: '9px 14px',
                cursor: expandable ? 'pointer' : 'default',
                opacity: hasCoord ? 1 : 0.55,
              }}
            >
              {/* 순번 배지 */}
              <div style={{
                flexShrink: 0,
                width: 22, height: 22,
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 700,
                marginTop: 1,
                background: seq == null ? 'rgba(255,255,255,0.1)'
                  : isActive ? '#f5a623'
                  : 'rgba(74,144,217,0.7)',
                color: seq == null ? 'rgba(255,255,255,0.3)' : 'white',
                border: isActive ? '2px solid #f5a623' : '2px solid transparent',
              }}>
                {seq != null ? seq : '·'}
              </div>

              {/* 사건명 + 장소명 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13,
                  color: isActive ? '#f5a623' : hasCoord ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.6)',
                  fontWeight: isActive ? 600 : 400,
                  lineHeight: 1.4,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {stop.nameKo || stop.title}
                </div>
                {stop.placeNameKo && (
                  <div style={{
                    fontSize: 11,
                    color: 'rgba(255,255,255,0.35)',
                    marginTop: 2,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {stop.placeNameKo}
                  </div>
                )}
              </div>

              {/* 펼침 토글 — 구절 있는 사건 행. 또렷한 보라 칩(SidePanel '📖 구절' 패턴). */}
              {expandable && (
                <span style={{
                  flexShrink: 0,
                  display: 'inline-flex', alignItems: 'center', gap: 3,
                  fontSize: 10, fontWeight: 700,
                  padding: '2px 7px', borderRadius: 999, lineHeight: 1.4,
                  marginTop: 1,
                  border: '1px solid #a78bfa',
                  background: expanded ? '#a78bfa' : 'rgba(167,139,250,0.14)',
                  color: expanded ? '#fff' : '#c4b5fd',
                }}>📖 {expanded ? '▾' : '▸'}</span>
              )}
            </div>

            {/* 펼친 사건의 근거구절 — 사건 아래에 들여써 "여정 > 사건 > 구절" 계층을 드러냄 */}
            {expanded && (
              <div onClick={(e) => e.stopPropagation()} style={{ padding: '0 12px 10px 30px' }}>
                <EventVerses eventId={stop.eventId} verseLang={verseLang} setVerseLang={setVerseLang} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
