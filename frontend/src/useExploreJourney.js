import { useState, useEffect } from 'react'
import { apiGet } from './api'

// 탐험(explore) 여정 데이터 상태·이펙트 — 정차지 목록·선택 정차지·투어 메타·인물 사건 목록.
//
// **이 훅은 App에서 호출해야 한다(ExploreStage 안이 아니다).** 이유: 탐험 6탭 중 "족보"는
// setExploreView가 아니라 openFamily로 전용 스테이지에 진입하고(useStageNavigation의 handleOpenFamily는
// activeStage만 'family'로 바꾸며 explorePersonId는 유지한다), App은 explore 블록을
// `activeStage === 'explore' && …`로 조건부 렌더하므로 **족보 탭에 들어가는 순간 ExploreStage가 언마운트된다.**
// 이 상태를 ExploreStage가 소유하면 언마운트와 함께 소실돼, 복귀 시 여정 재fetch + 정차지 선택 초기화라는
// 회귀가 생긴다(족보는 실사용 빈도가 높아 눈에 띈다). CONTEXT.md §화면 단계의 "유지해야 하는 상태는
// 컴포넌트 state로 못 지킨다"가 그대로 적용되는 자리 — **수명은 App 레벨, 코드만 이 훅**이다.
// 옮기지 말 것.
export function useExploreJourney({ explorePersonId, exploreTourId }) {
  // 여정 데이터 — 인물/투어 선택 시 한 번 fetch, MapView·JourneyList 공유
  const [journeyStops, setJourneyStops] = useState(null)
  // 탐험 중 투어의 제목 — /tour 응답에서 채움(내비 헤더·JourneyList·타임라인 라벨용)
  const [exploreTourName, setExploreTourName] = useState(null)
  // 투어 개요 메타 — /tour 응답의 subtitle·era·description(개요 탭용, task#222). 저작돼 있으나 버려지던 필드 소비.
  const [exploreTourMeta, setExploreTourMeta] = useState(null)
  // 인물 타임라인 필터 — explorePersonId 구동(선택 노드와 무관, tourEventIds와 대칭). 헌트 #10:
  // 노드 클릭에 소실되지 않도록 selectedNode가 아닌 탐험 인물에 묶는다.
  const [personEventIds, setPersonEventIds] = useState(null)
  const [activeStopIdx, setActiveStopIdx] = useState(null)

  useEffect(() => {
    let cancelled = false
    if (explorePersonId) {
      apiGet(`/person/${explorePersonId}/event-ids`)
        .then(data => { if (!cancelled) setPersonEventIds(new Set(data.eventIds)) })
        .catch(e => { if (!cancelled) { console.warn('[ExploreJourney] 인물 사건 목록 로드 실패', e); setPersonEventIds(null) } })
    } else {
      Promise.resolve().then(() => { if (!cancelled) setPersonEventIds(null) })
    }
    return () => { cancelled = true }
  }, [explorePersonId])

  useEffect(() => {
    const ctrl = new AbortController()
    if (explorePersonId) {
      apiGet(`/person/${explorePersonId}/journey`, { signal: ctrl.signal })
        .then(({ stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setExploreTourName(null); setExploreTourMeta(null) }) // async 콜백 — v7 OK
        .catch((e) => { if (e?.name !== 'AbortError') { console.warn('[ExploreJourney] 인물 여정 로드 실패', e); setJourneyStops([]) } })
    } else if (exploreTourId) {
      apiGet(`/tour/${exploreTourId}`, { signal: ctrl.signal })
        .then(({ title, subtitle, era, description, stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setExploreTourName(title); setExploreTourMeta({ subtitle, era, description }) })
        .catch((e) => { if (e?.name !== 'AbortError') { console.warn('[ExploreJourney] 투어 로드 실패', e); setJourneyStops([]) } })
    } else {
      // 인물·투어 모두 미선택 → 비동기로 초기화(effect 동기 setState 금지 규칙 회피)
      Promise.resolve().then(() => { setJourneyStops(null); setActiveStopIdx(null); setExploreTourName(null); setExploreTourMeta(null) })
    }
    return () => ctrl.abort()
  }, [explorePersonId, exploreTourId])

  return { journeyStops, activeStopIdx, setActiveStopIdx, exploreTourName, exploreTourMeta, personEventIds }
}
