import { useCallback, useEffect, useMemo, useState } from 'react'

// 투어 자동재생(playback) 시퀀서 훅 (task#223, ADR-0028). 해설 카드 UI는 TourPlayback.jsx.
// 사건 단위로 진행(좌표 없는 정차지도 건너뛰지 않음 — 카메라 유지·카드만 교체).
// 카메라·경로선은 App/MapView가 idx를 구독해 구동, 이 훅은 상태만.

// 자동 진행 간격 — note 길이 비례(최소 4초). 수동 이전/다음은 항상 가능.
function stepDuration(note) {
  return 4000 + (note ? Math.min(note.length * 35, 4000) : 0)
}

export function useTourPlayback(stops) {
  const [idx, setIdx] = useState(null) // 사건 인덱스(journeyStops 기준), null = 재생 모드 아님
  const [playing, setPlaying] = useState(false)
  const total = stops ? stops.length : 0

  // 자동 진행 타이머 — 마지막 정차지에서 자동 정지(재생 모드는 유지, 종료는 ✕).
  // setState는 타이머 콜백(비동기) 안에서만 호출 — effect 본문 동기 setState 회피(cascading render).
  useEffect(() => {
    if (!playing || idx == null || total === 0) return
    const t = setTimeout(() => {
      if (idx >= total - 1) setPlaying(false)
      else setIdx(i => i + 1)
    }, stepDuration(stops[idx]?.note))
    return () => clearTimeout(t)
  }, [playing, idx, stops, total])

  const start = useCallback(() => { setIdx(0); setPlaying(true) }, [])
  const exit = useCallback(() => { setIdx(null); setPlaying(false) }, [])
  const toggle = useCallback(() => setPlaying(p => !p), [])
  const next = useCallback(() => setIdx(i => (i == null ? 0 : Math.min(i + 1, total - 1))), [total])
  const prev = useCallback(() => setIdx(i => (i == null ? 0 : Math.max(i - 1, 0))), [])

  // 안정 참조(useMemo) — App의 이탈-종료 effect가 playback을 의존성으로 안전히 쓸 수 있게.
  return useMemo(
    () => ({ idx, playing, active: idx != null, start, exit, toggle, next, prev }),
    [idx, playing, start, exit, toggle, next, prev],
  )
}
