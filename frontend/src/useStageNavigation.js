import { useState, useEffect, useRef, useCallback } from 'react'
import { apiGet } from './api'
import { encodeHash, parseHash } from './urlState'

// 화면 단계(Stage)·URL·브라우저 히스토리 상태 머신 (ADR-0009 해시 딥링크 · ADR-0010 뒤로가기 통합).
// App.jsx에서 추출 — 이 파일은 lucide-react의 Map을 import하지 않고 useNodeSelection의 history(배열)를
// 구조분해하지 않으므로, 전역 Map/history 섀도잉 함정이 구조적으로 없다(과거 두 차례 런타임 크래시 원인).
// 노드 선택 원시값(selectedNode/selectNodeFresh/closePanel/handleNodeLoaded)은 useNodeSelection에서 주입받는다.
export function useStageNavigation({ selectedNode, selectNodeFresh, closePanel, handleNodeLoaded }) {
  // 'hub' | 'explore' | 'overview' | 'tours' | 'book'
  const [activeStage, setActiveStage] = useState('hub')
  // 책 상세 페이지의 대상 책 id — selectedNode와 분리(explorePersonId와 대칭). 책 페이지 안에서
  // 사건을 클릭해 시트를 띄워도(selectedNode 변경) 페이지 대상·URL이 흔들리지 않게 한다.
  const [bookId, setBookId] = useState(null)
  // 탐험 내 토글: 'map' | 'timeline'
  const [exploreView, setExploreView] = useState('map')
  // 탐험 중인 인물 — selectedNode와 분리해 장소 클릭 시에도 여정·맵 장소 기준 유지
  const [explorePersonId, setExplorePersonId] = useState(null)
  const [explorePersonName, setExplorePersonName] = useState(null)
  // 탐험 중인 테마 투어 id(=slug). 인물과 상호배타 — 하나가 세팅되면 다른 하나는 null.
  const [exploreTourId, setExploreTourId] = useState(null)

  // 딥링크(ADR-0009) — 해시 URL ↔ 내비 상태. 마운트 해시 캡처, 복원 1회, 이후 replaceState 반영.
  const initialHashRef = useRef(window.location.hash)
  const restoredRef = useRef(false)
  const curatedIdToSlug = useRef({})
  const curatedSlugToId = useRef({})
  // 히스토리 통합(ADR-0010) — 직전 nav-key 추적 + popstate 복원 중 재-push 방지.
  const navSyncRef = useRef({ initialized: false, stage: null, person: null, tour: null, book: null, sheetOpen: false })
  const popstateGuard = useRef(false)
  // 복원 완료 신호(state) — sync effect의 dep. ref가 아니라 state여야 복원 직후 베이스 엔트리 write가 트리거됨.
  const [restored, setRestored] = useState(false)

  // 큐레이션 인물 id 집합 — SidePanel '여정 탐험' CTA 노출 판단용.
  // 실패 시 CTA가 새로고침 전까지 조용히 사라지므로 유한 재시도(1s→2s→4s)로 자가 회복.
  const [curatedIds, setCuratedIds] = useState(null)
  // 큐레이션 nameKo→id — keyPeople(문자열)로만 등장하는 인물의 발자취 링크 해석용(id 없는 이름을 큐레이션 인물에 매칭).
  const [curatedNameToId, setCuratedNameToId] = useState(null)
  useEffect(() => {
    let timer, cancelled = false
    const load = attempt => {
      apiGet('/persons/curated')
        .then(list => {
          if (cancelled) return
          curatedIdToSlug.current = Object.fromEntries(list.map(p => [p.id, p.slug]))
          curatedSlugToId.current = Object.fromEntries(list.map(p => [p.slug, p.id]))
          setCuratedIds(new Set(list.map(p => p.id)))
          setCuratedNameToId(Object.fromEntries(list.map(p => [p.nameKo, p.id])))
        })
        .catch(() => {
          if (cancelled) return
          if (attempt < 3) timer = setTimeout(() => load(attempt + 1), 1000 * 2 ** attempt)
          else console.warn('/persons/curated 로드 실패 — 여정 탐험 CTA 미노출')
        })
    }
    load(0)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [])

  // 딥링크 복원 — curated(slug↔id) 준비되면 마운트 해시를 1회 파싱해 상태 복원.
  // setState는 마이크로태스크로 미룸(effect 동기 setState 금지 규칙).
  useEffect(() => {
    if (restoredRef.current) return
    const parsed = parseHash(initialHashRef.current)
    // person slug 해석만 curatedIds(slug↔id 맵)가 필요. overview/tours/tourSlug/hub는
    // curated 로드·실패와 무관하게 즉시 복원(#12: curated 실패 시 #/books·#/tours 고착 방지).
    if (parsed?.stage === 'explore' && parsed?.personSlug && !curatedIds) return
    restoredRef.current = true
    // 복원 상태 적용 후 같은 마이크로태스크에서 setRestored(true) — 그래야 sync effect의 베이스 write가
    // '복원된 stage'로 찍힌다(딥링크면 explore가 베이스). 깨진 해시(parsed null)도 허브 베이스로 복원 신호.
    Promise.resolve().then(() => {
      if (parsed) {
        if (parsed.stage === 'overview') setActiveStage('overview')
        else if (parsed.stage === 'book' && parsed.bookId) { setBookId(parsed.bookId); setActiveStage('book') }
        else if (parsed.stage === 'tours') setActiveStage('tours')
        else if (parsed.stage === 'explore' && parsed.tourSlug) {
          setExploreTourId(parsed.tourSlug); setActiveStage('explore'); setExploreView(parsed.exploreView)
        }
        else if (parsed.stage === 'explore' && parsed.personSlug) {
          const id = curatedSlugToId.current[parsed.personSlug]
          if (id) { selectNodeFresh(id); setExplorePersonId(id); setActiveStage('explore'); setExploreView(parsed.exploreView) }
          // 미지 slug → 허브 유지
        }
      }
      setRestored(true)
    })
    // curatedIds 준비 시 1회만 복원 — selectNodeFresh 등은 의도적으로 dep 제외(popstate effect와 동일 패턴).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curatedIds])

  // 히스토리 동기화(ADR-0010) — 딥링크 해시 미러 + 뒤로가기 통합.
  // push 조건: stage 변경 ∨ 인물 변경 ∨ 시트 열림(false→true). 그 외(뷰 토글·드릴 set→set·베이스)는 replace.
  // 시트 열림 = selectedNode가 있고 탐험 인물 자신이 아님(모바일 시트 표시 조건과 일치). node는 history.state에만.
  // 복원 완료 후에만 write(첫 렌더 hub write가 들어온 딥링크 해시를 덮어쓰는 것 방지).
  useEffect(() => {
    if (!restored) return
    const slug = explorePersonId ? curatedIdToSlug.current[explorePersonId] : null
    if (activeStage === 'explore' && !slug && !exploreTourId) return // slug/tour 미해결 시 깨진 URL 안 씀
    const sheetOpen = selectedNode != null && selectedNode !== explorePersonId
    const hash = encodeHash({ stage: activeStage, personSlug: slug, exploreView, tourSlug: exploreTourId, bookId })
    const state = { stage: activeStage, person: explorePersonId, tour: exploreTourId, book: bookId, view: exploreView, node: selectedNode }
    if (popstateGuard.current) {
      // popstate 복원 중 — 브라우저가 이미 히스토리를 옮겼으니 재-push 없이 ref만 동기화.
      popstateGuard.current = false
      navSyncRef.current = { initialized: true, stage: activeStage, person: explorePersonId, tour: exploreTourId, book: bookId, sheetOpen }
      return
    }
    const prev = navSyncRef.current
    const isForward = prev.initialized &&
      (prev.stage !== activeStage || prev.person !== explorePersonId || prev.tour !== exploreTourId || prev.book !== bookId || (!prev.sheetOpen && sheetOpen))
    navSyncRef.current = { initialized: true, stage: activeStage, person: explorePersonId, tour: exploreTourId, book: bookId, sheetOpen }
    if (isForward) window.history.pushState(state, '', hash)
    else window.history.replaceState(state, '', hash)
    // curatedIds 추가(#11): 카드 클릭이 slug맵 로드보다 빨라 :88에서 조기반환했더라도,
    // curatedIds null→Set 시 재실행돼 slug 해석 후 올바른 pushState가 찍히게 한다.
  }, [restored, activeStage, explorePersonId, exploreTourId, bookId, exploreView, selectedNode, curatedIds])

  // popstate — 브라우저/OS 뒤로·앞으로 시 event.state에서 내비 복원(가드로 재-push 방지).
  useEffect(() => {
    const onPop = (e) => {
      const s = e.state
      popstateGuard.current = true
      Promise.resolve().then(() => {
        if (!s) { setActiveStage('hub'); setExplorePersonId(null); setExplorePersonName(null); setExploreTourId(null); setBookId(null); closePanel(); return }
        setActiveStage(s.stage)
        setExplorePersonId(s.person ?? null)
        setExploreTourId(s.tour ?? null)
        setBookId(s.book ?? null)
        setExploreView(s.view || 'map')
        if (s.node) selectNodeFresh(s.node); else closePanel()
      })
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
    // 안정 setter + 최초 캡처 함수만 사용(내부는 안정 setState) — 마운트 1회 등록.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 인물 탐험 진입 — 탐험으로 전환 (투어와 상호배타). 착지 뷰는 호출부가 지정:
  // 허브 카드는 'intro'(소개), 여정 탐험 CTA·관계 뷰 상대 클릭은 기본 'map'(관계 뷰에서 상대 클릭 시 빈 관계 뷰로 빠지지 않게).
  function handleSelectPerson(id, view = 'map') {
    setExploreTourId(null)
    selectNodeFresh(id)
    setExplorePersonId(id)
    setExploreView(view)
    setActiveStage('explore')
  }

  // SidePanel에서 "이 곳을 지난 다른 인물" 칩 클릭 — 같은 탐험 단계에서 인물 전환 (투어 이탈)
  function handleExplorePerson(id) {
    setExploreTourId(null)
    setExplorePersonId(id)
    selectNodeFresh(id)
  }

  // 탐험에서 "다른 인물" 클릭 — 허브로 복귀, 선택 해제
  function handleBackToHub() {
    closePanel()
    setExplorePersonId(null)
    setExplorePersonName(null)
    setExploreTourId(null)
    setActiveStage('hub')
  }

  // 허브에서 "성경 책 둘러보기" 클릭
  function handleOpenOverview() {
    setActiveStage('overview')
  }

  // 개요에서 허브로 복귀
  function handleOverviewBack() {
    setActiveStage('hub')
  }

  // 개요에서 책 카드 클릭 — 책 상세 전용 전체화면 스테이지로 진입(오버레이 시트 아님).
  // exploreView는 'map'으로 리셋(이전 탐험의 relations/intro 잔상이 책 페이지의 사건 시트를 가리지 않게).
  function handleOpenBook(id) {
    closePanel()
    setBookId(id)
    setExploreView('map')
    setActiveStage('book')
  }

  // 책 페이지에서 개요로 복귀
  function handleBookBack() {
    closePanel()
    setBookId(null)
    setActiveStage('overview')
  }

  // 허브에서 "테마 투어" 클릭 — 투어 목록 스테이지
  function handleOpenTours() {
    setActiveStage('tours')
  }

  // 투어 목록에서 투어 선택 — 탐험 진입 (인물 대신 투어가 stops 공급, 인물과 상호배타)
  function handleSelectTour(id) {
    closePanel()
    setExplorePersonId(null)
    setExplorePersonName(null)
    setExploreTourId(id)
    setExploreView('map')  // 관계 뷰는 인물 전용 — 투어 진입 시 지도로 리셋
    setActiveStage('explore')
  }

  // 탐험(투어)에서 "테마 목록" 클릭 — 투어 목록으로 복귀
  function handleToursBack() {
    closePanel()
    setExploreTourId(null)
    setActiveStage('tours')
  }

  // SidePanel onNodeLoaded — 참조 안정화(useCallback). 인라인 화살표면 매 렌더 새 ref가 되어
  // SidePanel의 /node fetch effect(deps에 onNodeLoaded)가 매번 재실행→setCollapsed({}) 리셋으로
  // 섹션이 안 펼쳐지는 버그가 난다. explorePersonId 변경 시에만 갱신.
  const onNodeLoaded = useCallback((data) => {
    handleNodeLoaded(data)
    if (data.label === 'Person' && data.id === explorePersonId) setExplorePersonName(data.nameKo)
  }, [handleNodeLoaded, explorePersonId])

  // 시트 열림 파생 — 모바일 시트 표시 조건 및 history push 판단의 단일 출처.
  const sheetOpen = selectedNode != null && selectedNode !== explorePersonId

  return {
    activeStage, exploreView, explorePersonId, explorePersonName, exploreTourId, bookId, curatedIds, curatedNameToId, sheetOpen,
    setExploreView,
    selectPerson: handleSelectPerson,
    explorePerson: handleExplorePerson,
    backToHub: handleBackToHub,
    openOverview: handleOpenOverview,
    overviewBack: handleOverviewBack,
    openBook: handleOpenBook,
    bookBack: handleBookBack,
    openTours: handleOpenTours,
    selectTour: handleSelectTour,
    toursBack: handleToursBack,
    onNodeLoaded,
  }
}
