// 사이드 사건 리스트 — 여정 stops를 시간순으로 표시.
// props: stops(배열), activeStopIdx(number|null), onStopSelect(idx => void),
//        verseLang/setVerseLang(활성 정차지 근거구절 표시용)
// activeStopIdx는 buildJourneyStopsGeoJSON 기준 deduped 0-based 인덱스.
import { useEffect, useRef, useState } from 'react'
import EventVerses from './EventVerses'

export default function JourneyList({ stops, activeStopIdx, onStopSelect, verseLang, setVerseLang }) {
  const listRef = useRef(null)
  const activeRef = useRef(null)
  // 사용자가 직접 클릭한 정차지(eventId) — 같은 좌표 그룹에서 구절을 단 하나만 펼치기 위함.
  const [openEventId, setOpenEventId] = useState(null)

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

  // 활성 그룹(같은 좌표 정차지들) 중 구절을 펼칠 단 하나의 eventId —
  // 사용자가 직접 클릭한 것, 없으면(지도 배지·모바일 등 외부 활성화) 그룹의 첫 정차지.
  const activeGroupStops = withCoord.filter((s) => keyToIdx.get(coKey(s)) === activeStopIdx)
  const shownEventId = activeGroupStops.some((s) => s.eventId === openEventId)
    ? openEventId
    : (activeGroupStops[0]?.eventId ?? null)

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
                if (!hasCoord || dedupIdx == null) return
                onStopSelect(dedupIdx)
                setOpenEventId(stop.eventId)
              }}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                padding: '9px 14px',
                cursor: hasCoord ? 'pointer' : 'default',
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

            {/* 활성 정차지 근거구절 — 클릭한 단 하나의 정차지만 펼친다(같은 좌표 그룹이라도). */}
            {isActive && stop.eventId === shownEventId && (
              <div onClick={(e) => e.stopPropagation()} style={{ padding: '2px 12px 10px' }}>
                <EventVerses eventId={stop.eventId} verseLang={verseLang} setVerseLang={setVerseLang} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
