// 사이드 사건 리스트 — 여정 stops를 시간순으로 표시.
// props: stops(배열), activeStopIdx(number|null), onStopSelect(idx => void)
// activeStopIdx는 buildJourneyStopsGeoJSON 기준 deduped 0-based 인덱스.
import { useEffect, useRef } from 'react'

export default function JourneyList({ stops, activeStopIdx, onStopSelect }) {
  const listRef = useRef(null)
  const activeRef = useRef(null)

  // 활성 항목 자동 스크롤
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
  const dedupedMap = new Map()
  for (const s of withCoord) {
    const k = coKey(s)
    if (!dedupedMap.has(k)) seen.push(k)
    dedupedMap.set(k, s)
  }
  // stopKey → deduped index
  const keyToIdx = new Map(seen.map((k, i) => [k, i]))

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
        // 장소(정차지) 번호 — 지도 배지와 동일 체계(같은 장소는 같은 번호, 재방문도 동일)
        const stopNo = dedupIdx != null ? dedupIdx + 1 : null

        return (
          <div
            key={stop.eventId ?? rawIdx}
            ref={isActive ? activeRef : null}
            onClick={() => {
              if (!hasCoord || dedupIdx == null) return
              onStopSelect(dedupIdx)
            }}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
              padding: '9px 14px',
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              background: isActive ? 'rgba(124,156,252,0.15)' : 'transparent',
              cursor: hasCoord ? 'pointer' : 'default',
              transition: 'background 0.15s',
              opacity: hasCoord ? 1 : 0.45,
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
              background: stopNo == null ? 'rgba(255,255,255,0.1)'
                : isActive ? '#f5a623'
                : 'rgba(74,144,217,0.7)',
              color: stopNo == null ? 'rgba(255,255,255,0.3)' : 'white',
              border: isActive ? '2px solid #f5a623' : '2px solid transparent',
            }}>
              {stopNo != null ? stopNo : '·'}
            </div>

            {/* 사건명 + 장소명 */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 13,
                color: isActive ? '#f5a623' : hasCoord ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.45)',
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
          </div>
        )
      })}
    </div>
  )
}
