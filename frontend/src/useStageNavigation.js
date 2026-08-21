import { useState, useEffect, useRef, useCallback } from 'react'
import { apiGet } from './api'
import { encodeHash, parseHash, isNoTarget } from './urlState'

// 화면 단계(Stage)·URL·브라우저 히스토리 상태 머신 (ADR-0009 해시 딥링크 · ADR-0010 뒤로가기 통합).
// App.jsx에서 추출 — 이 파일은 lucide-react의 Map을 import하지 않고 useNodeSelection의 history(배열)를
// 구조분해하지 않으므로, 전역 Map/history 섀도잉 함정이 구조적으로 없다(과거 두 차례 런타임 크래시 원인).
// 노드 선택 원시값(selectedNode/selectNodeFresh/closePanel/handleNodeLoaded)은 useNodeSelection에서 주입받는다.
export function useStageNavigation({ selectedNode, selectNodeFresh, closePanel, handleNodeLoaded }) {
  // 'intro' | 'hub' | 'explore' | 'overview' | 'tours' | 'book' | 'family'
  // 인트로(task#239) — 무해시 진입 + 켜짐(biblemap-intro !== 'off')이면 허브 대신 인트로가 시작 화면.
  // 딥링크(해시 있음)는 무조건 스킵. 무타깃 판정은 urlState의 isNoTarget 하나만 쓴다 — 이 초기값이
  // 유지되는 것은 아래 마운트 복원 effect가 **같은 술어로** 무타깃을 걸러내고 나가기 때문이다(task#281).
  // (그전엔 이 자리에 "복원 effect는 hub 해시에 activeStage를 건드리지 않는다"고 적혀 있었는데 정확히
  //  그 반대였다 — 그 effect가 초기값을 허브로 덮고 있었다. 그래서 게이트를 옆에 뒀다.)
  const [activeStage, setActiveStage] = useState(() => {
    return isNoTarget(window.location.hash) && localStorage.getItem('biblemap-intro') !== 'off' ? 'intro' : 'hub'
  })
  // 책 상세 페이지의 대상 책 id — selectedNode와 분리(explorePersonId와 대칭). 책 페이지 안에서
  // 사건을 클릭해 시트를 띄워도(selectedNode 변경) 페이지 대상·URL이 흔들리지 않게 한다.
  const [bookId, setBookId] = useState(null)
  // 가계도 페이지의 대상(focus) 인물 id — bookId와 동형으로 selectedNode와 분리. 트리 노드를
  // 클릭해 재중심화하면 familyId만 바뀌어 페이지·URL이 안정적으로 그 인물로 옮겨간다.
  const [familyId, setFamilyId] = useState(null)
  // 장소 페이지 대상 id(task#270) — bookId와 대칭(전용 전체화면 스테이지)
  const [placeId, setPlaceId] = useState(null)
  // 단어 분포 페이지의 대상 책 id('all' 포함) — bookId·familyId와 동형.
  const [wordsBookId, setWordsBookId] = useState(null)
  // 본문 리더의 대상 책 id·장 번호(null = 장 그리드) — wordsBookId와 동형(task#205).
  const [readerBookId, setReaderBookId] = useState(null)
  const [readerChapter, setReaderChapter] = useState(null)
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
  const navSyncRef = useRef({ initialized: false, stage: null, person: null, tour: null, book: null, family: null, reader: null, chapter: null, sheetOpen: false })
  const popstateGuard = useRef(false)
  // 복원 완료 신호(state) — sync effect의 dep. ref가 아니라 state여야 복원 직후 베이스 엔트리 write가 트리거됨.
  const [restored, setRestored] = useState(false)

  // 큐레이션 인물 id 집합 — SidePanel '여정 탐험' CTA 노출 판단용.
  // 실패 시 CTA가 새로고침 전까지 조용히 사라지므로 유한 재시도(1s→2s→4s)로 자가 회복.
  const [curatedIds, setCuratedIds] = useState(null)
  // id → slug 렌더용 state 맵(인장 등 표시용 — ref 맵은 렌더 중 접근 금지라 별도 보관)
  const [curatedSlugById, setCuratedSlugById] = useState(null)
  // id → era 맵(비유·기적 신약 게이트용, task#256) — era 원천은 백엔드 _ERA(/persons/curated 응답)
  const [curatedEraById, setCuratedEraById] = useState(null)
  useEffect(() => {
    let timer, cancelled = false
    const load = attempt => {
      apiGet('/persons/curated')
        .then(list => {
          if (cancelled) return
          curatedIdToSlug.current = Object.fromEntries(list.map(p => [p.id, p.slug]))
          curatedSlugToId.current = Object.fromEntries(list.map(p => [p.slug, p.id]))
          setCuratedSlugById(curatedIdToSlug.current)
          setCuratedEraById(Object.fromEntries(list.map(p => [p.id, p.era])))
          setCuratedIds(new Set(list.map(p => p.id)))
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

  // keyPeople 완성 카드 맵 (book_tid → {name → {kind, journeyId, role, intro, verses}}). ADR-0018.
  // 실패 시 keyPeople가 칩 없이 평문으로 남으므로 조용히 폴백.
  const [keyPeopleCards, setKeyPeopleCards] = useState(null)
  useEffect(() => {
    let cancelled = false
    apiGet('/keypeople-cards')
      .then(map => { if (!cancelled) setKeyPeopleCards(map) })
      .catch(() => { if (!cancelled) console.warn('/keypeople-cards 로드 실패 — keyPeople 칩 미노출') })
    return () => { cancelled = true }
  }, [])

  // 파싱된 해시 → 상태 적용. 딥링크 복원과 저장·이어보기 카드 복원(task#268)의 공용 경로.
  function applyParsedHash(parsed) {
    if (parsed.stage === 'intro') setActiveStage('intro')
    else if (parsed.stage === 'overview') setActiveStage('overview')
    else if (parsed.stage === 'book' && parsed.bookId) { setBookId(parsed.bookId); setActiveStage('book') }
    else if (parsed.stage === 'family' && parsed.familyId) { setFamilyId(parsed.familyId); setActiveStage('family') }
    else if (parsed.stage === 'place' && parsed.placeId) { setPlaceId(parsed.placeId); setActiveStage('place') }
    else if (parsed.stage === 'words' && parsed.wordsBookId) { setWordsBookId(parsed.wordsBookId); setActiveStage('words') }
    else if (parsed.stage === 'reader' && parsed.readerBookId) { setReaderBookId(parsed.readerBookId); setReaderChapter(parsed.readerChapter ?? null); setActiveStage('reader') }
    else if (parsed.stage === 'canon') setActiveStage('canon')
    else if (parsed.stage === 'stats') setActiveStage('stats')
    else if (parsed.stage === 'topics') setActiveStage('topics')
    else if (parsed.stage === 'tours') setActiveStage('tours')
    else if (parsed.stage === 'hub') { setExplorePersonId(null); setExploreTourId(null); setActiveStage('hub') }
    else if (parsed.stage === 'explore' && parsed.tourSlug) {
      setExploreTourId(parsed.tourSlug); setExplorePersonId(null); setActiveStage('explore'); setExploreView(parsed.exploreView)
    }
    else if (parsed.stage === 'explore' && parsed.personSlug) {
      const id = curatedSlugToId.current[parsed.personSlug]
      if (id) { selectNodeFresh(id); setExplorePersonId(id); setExploreTourId(null); setActiveStage('explore'); setExploreView(parsed.exploreView) }
      // 미지 slug → 허브 유지
    }
  }

  // 저장·이어보기 카드 복원(task#268) — 문서 안에서 해시만 바꾸면 스테이지가 리마운트되지 않으므로
  // 상태 머신을 직접 태운다(히스토리 해시는 sync effect가 뒤따라 맞춘다).
  function handleGoToHash(hash) {
    const parsed = parseHash(hash)
    if (!parsed) return
    closePanel()
    applyParsedHash(parsed)
  }

  // 딥링크 복원 — curated(slug↔id) 준비되면 마운트 해시를 1회 파싱해 상태 복원.
  // setState는 마이크로태스크로 미룸(effect 동기 setState 금지 규칙).
  useEffect(() => {
    if (restoredRef.current) return
    // 무타깃 진입은 딥링크가 아니다 — 이 effect의 계약은 딥링크 복원이므로 여기서 걸러내고 나간다.
    // 걸러내지 않으면 parseHash('')의 {stage:'hub'}가 applyParsedHash를 타고 초기값 'intro'를 덮는다
    // (task#281의 결함). 마운트 직후라 applyParsedHash의 hub 분기가 하는 초기화(explorePerson/tour
    // null)는 이미 그 상태이므로 건너뛰어도 잃는 것이 없다. setRestored만 태워 sync effect의 베이스
    // 엔트리 write(#/intro 또는 #/)를 트리거한다.
    if (isNoTarget(initialHashRef.current)) {
      restoredRef.current = true
      Promise.resolve().then(() => setRestored(true))
      return
    }
    const parsed = parseHash(initialHashRef.current)
    // person slug 해석만 curatedIds(slug↔id 맵)가 필요. overview/tours/tourSlug/hub는
    // curated 로드·실패와 무관하게 즉시 복원(#12: curated 실패 시 #/books·#/tours 고착 방지).
    if (parsed?.stage === 'explore' && parsed?.personSlug && !curatedIds) return
    restoredRef.current = true
    // 복원 상태 적용 후 같은 마이크로태스크에서 setRestored(true) — 그래야 sync effect의 베이스 write가
    // '복원된 stage'로 찍힌다(딥링크면 explore가 베이스). 깨진 해시(parsed null)도 허브 베이스로 복원 신호.
    Promise.resolve().then(() => {
      if (parsed) applyParsedHash(parsed)
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
    const hash = encodeHash({ stage: activeStage, personSlug: slug, exploreView, tourSlug: exploreTourId, bookId, familyId, wordsBookId, readerBookId, readerChapter, placeId })
    const state = { stage: activeStage, person: explorePersonId, tour: exploreTourId, book: bookId, family: familyId, words: wordsBookId, reader: readerBookId, chapter: readerChapter, place: placeId, view: exploreView, node: selectedNode }
    if (popstateGuard.current) {
      // popstate 복원 중 — 브라우저가 이미 히스토리를 옮겼으니 재-push 없이 ref만 동기화.
      popstateGuard.current = false
      navSyncRef.current = { initialized: true, stage: activeStage, person: explorePersonId, tour: exploreTourId, book: bookId, family: familyId, words: wordsBookId, reader: readerBookId, chapter: readerChapter, place: placeId, sheetOpen }
      return
    }
    const prev = navSyncRef.current
    const isForward = prev.initialized &&
      (prev.stage !== activeStage || prev.person !== explorePersonId || prev.tour !== exploreTourId || prev.book !== bookId || prev.family !== familyId || prev.words !== wordsBookId || prev.reader !== readerBookId || prev.chapter !== readerChapter || prev.place !== placeId || (!prev.sheetOpen && sheetOpen))
    navSyncRef.current = { initialized: true, stage: activeStage, person: explorePersonId, tour: exploreTourId, book: bookId, family: familyId, words: wordsBookId, reader: readerBookId, chapter: readerChapter, place: placeId, sheetOpen }
    if (isForward) window.history.pushState(state, '', hash)
    else window.history.replaceState(state, '', hash)
    // curatedIds 추가(#11): 카드 클릭이 slug맵 로드보다 빨라 :88에서 조기반환했더라도,
    // curatedIds null→Set 시 재실행돼 slug 해석 후 올바른 pushState가 찍히게 한다.
  }, [restored, activeStage, explorePersonId, exploreTourId, bookId, familyId, wordsBookId, readerBookId, readerChapter, placeId, exploreView, selectedNode, curatedIds])

  // popstate — 브라우저/OS 뒤로·앞으로 시 event.state에서 내비 복원(가드로 재-push 방지).
  useEffect(() => {
    const onPop = (e) => {
      const s = e.state
      popstateGuard.current = true
      Promise.resolve().then(() => {
        if (!s) {
          // state:null은 두 가지가 뭉뚱그려진 값이다 — ① 히스토리 시작점, ② 동일문서 프래그먼트
          // 내비게이션(주소창에 다른 딥링크 해시를 붙여넣기)이 만든 무상태 엔트리. ②도 popstate를
          // state:null로 발화시키므로, 구분 없이 허브로 리셋하면 URL이 가리키는 화면 대신 허브가
          // 뜬다(3차 헌트 C4). state가 없어도 URL은 항상 신뢰 가능한 진실이므로 먼저 재해석한다.
          // 무타깃 판정은 정본 술어만 쓴다(ADR 260821-000937 — 판정 지점은 정본 밖 0곳).
          const raw = window.location.hash
          const parsed = isNoTarget(raw) ? null : parseHash(raw)
          if (parsed) { closePanel(); applyParsedHash(parsed); return }
          setActiveStage('hub'); setExplorePersonId(null); setExplorePersonName(null); setExploreTourId(null); setBookId(null); setFamilyId(null); setWordsBookId(null); setReaderBookId(null); setReaderChapter(null); setPlaceId(null); closePanel(); return
        }
        setActiveStage(s.stage)
        setExplorePersonId(s.person ?? null)
        setExploreTourId(s.tour ?? null)
        setBookId(s.book ?? null)
        setFamilyId(s.family ?? null)
        setWordsBookId(s.words ?? null)
        setReaderBookId(s.reader ?? null)
        setReaderChapter(s.chapter ?? null)
        setPlaceId(s.place ?? null)
        setExploreView(s.view || 'map')
        if (s.node) selectNodeFresh(s.node); else closePanel()
      })
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
    // 안정 setter + 최초 캡처 함수만 사용(내부는 안정 setState) — 마운트 1회 등록.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 통사 연표 진입/복귀(task#271) — 스테이지만 바뀌는 단일 화면(통계·주제 성구와 동형).
  function handleOpenCanon() {
    closePanel()
    setActiveStage('canon')
  }

  function handleCanonBack() {
    window.history.back()
  }

  // 장소 페이지 진입(task#270) — 지도 마커·정차지·상세 시트 어디서든. 전용 전체화면(책 상세와 같은 패턴).
  function handleOpenPlace(id) {
    if (!id) return
    closePanel()
    setPlaceId(id)
    setActiveStage('place')
  }

  // 장소 페이지 복귀 — 히스토리 위임(ADR-0010 관행). 직전 화면으로 정확히 돌아간다.
  function handlePlaceBack() {
    window.history.back()
  }

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

  // 헤더 ⓘ 소개 버튼 — 어느 화면에서든 인트로 재열람(끈 뒤 재진입 경로, task#239)
  function handleOpenIntro() {
    closePanel()
    setActiveStage('intro')
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

  // 가계도 페이지 진입 — 인물 상세에서 "가계도" 클릭. 대상 인물을 focus로.
  // exploreView는 'map'으로 리셋(bookId 진입과 동형 — 이전 뷰 잔상 방지).
  function handleOpenFamily(id) {
    closePanel()
    setFamilyId(id)
    setExploreView('map')
    setActiveStage('family')
  }

  // 가계도 트리 노드 클릭 — 같은 스테이지에서 focus 인물만 교체(재중심화).
  function handleRecenterFamily(id) {
    setFamilyId(id)
  }

  // 가계도에서 뒤로 — 진입 지점이 다양하므로 브라우저 히스토리에 위임(ADR-0010).
  function handleFamilyBack() {
    window.history.back()
  }

  // 단어 분포 페이지 진입 — 책 상세의 "단어 분포" 버튼(또는 딥링크). 대상 책('all' 가능)을 focus로.
  function handleOpenWords(id) {
    closePanel()
    setWordsBookId(id)
    setExploreView('map')
    setActiveStage('words')
  }

  // 페이지 내 책 선택 드롭다운 — 같은 스테이지에서 대상 책만 교체(가계도 재중심화와 동형).
  function handleSelectWordsBook(id) {
    setWordsBookId(id)
  }

  // 단어 분포에서 뒤로 — 진입 지점(책 상세/딥링크)에 무관하게 브라우저 히스토리 위임(가계도와 동형).
  function handleWordsBack() {
    window.history.back()
  }

  // 통계 페이지 진입 — 개요 "통계" 탭(또는 딥링크). exploreView는 'map'으로 리셋(words·family와 동형).
  function handleOpenStats() {
    closePanel()
    setExploreView('map')
    setActiveStage('stats')
  }

  // 통계에서 뒤로 — 진입 지점에 무관하게 브라우저 히스토리 위임(단어 분포와 동형).
  function handleStatsBack() {
    window.history.back()
  }

  // 주제 성구 페이지 진입 — 개요 "주제 성구" 탭(또는 딥링크). 통계와 동형(대상 id 없는 고정 뷰).
  function handleOpenTopics() {
    closePanel()
    setExploreView('map')
    setActiveStage('topics')
  }

  // 주제 성구에서 뒤로 — 진입 지점에 무관하게 브라우저 히스토리 위임(통계와 동형).
  function handleTopicsBack() {
    window.history.back()
  }

  // 본문 리더 진입 — 책 상세 "본문 읽기" 탭(또는 딥링크). 장 미지정(null)이면 장 그리드(task#205).
  function handleOpenReader(id, chapter = null) {
    closePanel()
    setReaderBookId(id)
    setReaderChapter(chapter)
    setExploreView('map')
    setActiveStage('reader')
  }

  // 장 이동(그리드→본문·이전/다음 장·목차 복귀 null) — 같은 스테이지에서 장만 교체(단어 분포 책 교체와 동형).
  function handleSelectChapter(n) {
    setReaderChapter(n)
  }

  // 리더에서 뒤로 — 진입 지점에 무관하게 브라우저 히스토리 위임(단어 분포와 동형).
  function handleReaderBack() {
    window.history.back()
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
    setExploreView('intro')  // 투어 진입은 개요 탭부터(task#222) — 인물 전용 뷰(관계 등) 잔상도 함께 해소
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

  // 큐레이션 id → slug 해석(인장 심볼 조회용) — 기존 딥링크 맵 ref 재사용, 미등록이면 null(심볼 폴백).
  const getPersonSlug = (id) => curatedIdToSlug.current[id] ?? null

  return {
    activeStage, exploreView, explorePersonId, explorePersonName, exploreTourId, bookId, familyId, wordsBookId, readerBookId, readerChapter, placeId, curatedIds, keyPeopleCards, sheetOpen,
    // 탐험 인물 slug — 인장 렌더 등 표시용(state 맵에서 파생 — 렌더 중 ref 접근 금지)
    explorePersonSlug: explorePersonId ? (curatedSlugById?.[explorePersonId] ?? null) : null,
    // 탐험 인물 era — 비유·기적 신약 게이트용(task#256)
    explorePersonEra: explorePersonId ? (curatedEraById?.[explorePersonId] ?? null) : null,
    setExploreView,
    selectPerson: handleSelectPerson,
    explorePerson: handleExplorePerson,
    backToHub: handleBackToHub,
    openIntro: handleOpenIntro,
    openOverview: handleOpenOverview,
    overviewBack: handleOverviewBack,
    openBook: handleOpenBook,
    bookBack: handleBookBack,
    openFamily: handleOpenFamily,
    recenterFamily: handleRecenterFamily,
    familyBack: handleFamilyBack,
    openWords: handleOpenWords,
    selectWordsBook: handleSelectWordsBook,
    wordsBack: handleWordsBack,
    openStats: handleOpenStats,
    statsBack: handleStatsBack,
    openTopics: handleOpenTopics,
    topicsBack: handleTopicsBack,
    goToHash: handleGoToHash,
    openPlace: handleOpenPlace,
    openCanon: handleOpenCanon,
    canonBack: handleCanonBack,
    placeBack: handlePlaceBack,
    openReader: handleOpenReader,
    selectChapter: handleSelectChapter,
    readerBack: handleReaderBack,
    openTours: handleOpenTours,
    selectTour: handleSelectTour,
    toursBack: handleToursBack,
    onNodeLoaded,
    getPersonSlug,
  }
}
