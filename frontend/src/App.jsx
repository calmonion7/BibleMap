import { useState, useEffect, useRef, useMemo } from 'react'
import { BookOpen, BarChart3, ScrollText, PieChart, Quote, MapPin, CalendarRange } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import SidePanel from './SidePanel'
import BibleOverviewView from './BibleOverviewView'
import PersonHub from './PersonHub'
import IntroView from './IntroView'
import SpineHeader, { HEADER_H, RIBBON_OVERHANG } from './SpineHeader'
import StageNav, { NAV_H } from './StageNav'
import ExploreStage from './ExploreStage'
import { useExploreJourney } from './useExploreJourney'
import { useTourPlayback } from './useTourPlayback'
import PersonSymbol from './personSymbols'
import FamilyTree from './FamilyTree'
import WordDistributionView from './WordDistributionView'
import StatsView from './StatsView'
import TopicalVersesView from './TopicalVersesView'
import ChapterReader from './ChapterReader'
import SearchPanel from './SearchPanel'
import { useBookmarks } from './useBookmarks'
import { useReadingProgress } from './useReadingProgress'
import PlaceView from './PlaceView'
import CanonTimelineView from './CanonTimelineView'
import TourList from './TourList'
import { MOBILE_BREAKPOINT, SHEET_VH } from './constants'
import { useNodeSelection } from './useNodeSelection'
import { useStageNavigation } from './useStageNavigation'
import { apiGet } from './api'

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT}px)`

function App() {
  // 절 본문 표시 언어('ko'|'en', 기본 ko) — 타임라인·SidePanel 공유.
  const [verseLang, setVerseLang] = useState('ko')
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)

  const {
    selectedNode, selectedNodeMeta, history,
    handleNodeLoaded, selectNode, selectNodeFresh, goBack, closePanel,
  } = useNodeSelection()

  // 화면 단계(Stage)·URL·브라우저 히스토리 상태 머신 — 노드 선택 원시값을 주입(useStageNavigation).
  const {
    activeStage, exploreView, explorePersonId, explorePersonName, explorePersonSlug, explorePersonEra, exploreTourId, bookId, familyId, wordsBookId, readerBookId, readerChapter, placeId, curatedIds, keyPeopleCards, sheetOpen,
    setExploreView, selectPerson, explorePerson, backToHub, openIntro, openOverview, overviewBack,
    openTours, selectTour, toursBack, openBook, bookBack, openFamily, recenterFamily, familyBack,
    openWords, selectWordsBook, wordsBack, openReader, selectChapter, readerBack, goToHash, openPlace, placeBack, openCanon, canonBack, openStats, statsBack, openTopics, topicsBack, onNodeLoaded, getPersonSlug,
  } = useStageNavigation({ selectedNode, selectNodeFresh, closePanel, handleNodeLoaded })

  // 개인화 저장 계층(task#268) — 이 기기에만 남는 북마크·이어보기(ADR 260819-191704).
  // 훅 인스턴스는 App에 하나만 둔다(여러 곳에서 각자 호출하면 토글이 서로에게 즉시 반영되지 않는다).
  const { bookmarks, recent, toggleBookmark, recordRecent } = useBookmarks()
  // 읽기 진도(task#269) — 같은 이유로 App에 인스턴스 하나(리더·개요·허브가 같은 상태를 본다).
  const { isRead, toggleRead, bookReadCount, resume } = useReadingProgress()

  // 지금 화면의 저장 항목 — 뷰 토글로 항목이 갈라지지 않게 스테이지 단위 기본 해시를 쓴다.
  const bookmarkEntry = useMemo(() => {
    if (activeStage === 'explore' && explorePersonSlug) return { hash: `#/person/${explorePersonSlug}`, type: 'person', label: explorePersonSlug }
    if (activeStage === 'explore' && exploreTourId) return { hash: `#/tour/${exploreTourId}`, type: 'tour', label: exploreTourId }
    if (activeStage === 'reader' && readerBookId) {
      return { hash: readerChapter ? `#/read/${readerBookId}/${readerChapter}` : `#/read/${readerBookId}`, type: 'reader', label: readerBookId }
    }
    return null
  }, [activeStage, explorePersonSlug, exploreTourId, readerBookId, readerChapter])

  const isBookmarked = !!bookmarkEntry && bookmarks.some(b => b.hash === bookmarkEntry.hash)

  // 통합 검색(task#267) — 헤더 버튼과 `/` 단축키로 여는 전역 오버레이.
  const [searchOpen, setSearchOpen] = useState(false)
  // 검색 결과로 들어온 절 — 리더가 이 절을 강조하고 뷰포트로 스크롤한다. 장을 옮기면 해제.
  const [highlightVerseId, setHighlightVerseId] = useState(null)

  useEffect(() => {
    function onKey(e) {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return
      // 입력 중에는 `/`가 문자다 — 텍스트 입력·편집 가능 영역에서는 가로채지 않는다.
      const t = e.target
      if (t?.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t?.tagName)) return
      e.preventDefault()
      setSearchOpen(true)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // 이름 결과 — 큐레이션 인물은 인물 탐험으로, 그 밖의 노드는 상세 시트로(기존 두 경로 재사용).
  function handleSearchNode(n) {
    setSearchOpen(false)
    if (n.label === 'Person' && curatedIds?.has(n.id)) selectPerson(n.id, 'intro')
    else selectNode(n.id)
  }

  // 구절 결과 — 그 장의 리더를 열고 해당 절을 강조한다.
  function handleSearchVerse(v) {
    setSearchOpen(false)
    setHighlightVerseId(v.verseId)
    openReader(v.bookId, v.chapter)
  }

  // 여정 데이터 상태 — 코드는 useExploreJourney, **수명은 App**(족보 스테이지 진입 시 ExploreStage가
  // 언마운트되므로 여기서 소유해야 복귀 시 재fetch·정차지 초기화가 없다. 훅 상단 주석 참조).
  const journey = useExploreJourney({ explorePersonId, exploreTourId })
  // 투어 자동재생(task#223) 상태 — 같은 이유로 App 소유(task#263). ExploreStage가 헤더 리본 이탈→뒤로가기로
  // 재마운트돼도 재생 idx·playing이 살아남는다(이전엔 ExploreStage 로컬 state라 재마운트 시 소실됐다).
  const playback = useTourPlayback(journey.journeyStops)

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  const swipeStartY = useRef(null)
  const sheetAtTop = useRef(false)
  function onSheetTouchStart(e) {
    swipeStartY.current = e.touches[0].clientY
    sheetAtTop.current = e.currentTarget.scrollTop <= 0
  }
  function onSheetTouchEnd(e) {
    if (swipeStartY.current == null) return
    const dy = e.changedTouches[0].clientY - swipeStartY.current
    // 시트가 스크롤된 상태의 하향 드래그는 콘텐츠 스크롤 제스처 — 최상단에서 시작한 pull-down만 닫는다
    // 닫기는 history.back()에 위임(ADR-0010) — 뒤로가기와 동일 경로로 시트 열림 엔트리를 pop.
    if (dy > 80 && sheetAtTop.current) window.history.back()
    swipeStartY.current = null
  }

  // 정경 순서 내비(task#211) — 책 상세 이전/다음 권. /books-overview 순서 재사용(신규 API 없음), 첫 book 진입 시 1회 로드.
  const [booksOrder, setBooksOrder] = useState(null)
  useEffect(() => {
    if (activeStage !== 'book' || booksOrder) return
    let cancelled = false
    apiGet('/books-overview')
      .then(list => { if (!cancelled) setBooksOrder(list.map(b => ({ id: b.id, nameKo: b.nameKo }))) })
      .catch(e => { if (!cancelled) console.warn('[App] 책 목록 로드 실패 — 정경 내비 미노출', e) })
    return () => { cancelled = true }
  }, [activeStage, booksOrder])

  // 책등 헤더의 활성 부(部) — 개요·책·단어·리더는 '성경책', 투어 목록·투어 탐험은 '투어', 나머지는 '인물'(ADR-0026)
  const activeSection =
    activeStage === 'intro' ? null // 인트로는 어느 부(部)도 아님 — 리본 전체 비활성
      : activeStage === 'overview' || activeStage === 'book' || activeStage === 'words' || activeStage === 'reader' || activeStage === 'stats' || activeStage === 'topics' || activeStage === 'canon' ? 'books'
        : activeStage === 'tours' || (activeStage === 'explore' && exploreTourId != null) ? 'tours'
          : 'persons'

  // 리본 클릭 — 기존 내비 콜백 조합만(상태 머신·URL 무변경). 탐험 중 열린 시트가 새 부로 넘어오지 않게 closePanel 동반.
  function handleSelectSection(key) {
    if (key === 'persons') backToHub()
    else if (key === 'books') { closePanel(); openOverview() }
    else { closePanel(); openTours() }
  }
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100dvh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

      {/* 책등 전역 헤더 — 전 스테이지 상시 표시, 리본 3부 + 테마 토글(ADR-0026) */}
      <SpineHeader
        activeSection={activeSection}
        onSelectSection={handleSelectSection}
        onOpenIntro={openIntro}
        onOpenSearch={() => setSearchOpen(true)}
        isMobile={isMobile}
      />

      {/* 책갈피 리본이 헤더 아래로 드리워지는 만큼의 여백 — 리본 꼬리가 스테이지 내비 탭을 덮지 않게(ADR-0026) */}
      <div style={{ height: RIBBON_OVERHANG, flexShrink: 0, background: 'var(--bg-1)' }} />

      {/* 인트로 단계 — 무해시 첫 진입의 기능 소개 관문(task#239). 온오프·재진입은 IntroView·헤더 ⓘ */}
      {activeStage === 'intro' && (
        <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          <IntroView
            isMobile={isMobile}
            onStart={backToHub}
            onOpenTours={openTours}
            onOpenOverview={openOverview}
          />
        </div>
      )}

      {/* 허브 단계 — 인물 선택 전 */}
      {activeStage === 'hub' && (
        <div className="stage-in" style={{ flex: 1, overflow: 'hidden' }}>
          <PersonHub
            onSelectPerson={(id) => selectPerson(id, 'intro')}
            bookmarks={bookmarks}
            recent={recent}
            onOpenSaved={goToHash}
            resume={resume}
            onResumeReading={r => openReader(r.bookId, r.chapter)}
          />
        </div>
      )}

      {/* 개요 단계 — 허브에서 진입 */}
      {activeStage === 'overview' && (
        <>
          <StageNav onBack={overviewBack} backLabel="인물 허브">
            <StageNav.Tab icon={BookOpen} label="책 둘러보기" active />
            <StageNav.Tab icon={BarChart3} label="단어 분포" onClick={() => openWords('all')} />
            <StageNav.Tab icon={PieChart} label="통계" onClick={openStats} />
            <StageNav.Tab icon={Quote} label="주제 성구" onClick={openTopics} />
            <StageNav.Tab icon={CalendarRange} label="통사 연표" onClick={openCanon} />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <BibleOverviewView
              onSelectNode={openBook}
              selectedNode={bookId}
              verseLang={verseLang}
              setVerseLang={setVerseLang}
              bookReadCount={bookReadCount}
            />
          </div>
        </>
      )}

      {/* 책 상세 단계 — 개요에서 책 카드 클릭 시 진입. 시트/우측 패널이 아닌 전용 전체화면 페이지(인물 소개 뷰와 같은 패턴). */}
      {activeStage === 'book' && (
        <>
          <StageNav onBack={bookBack} backLabel="성경 책 둘러보기">
            <StageNav.Tab icon={BookOpen} label="책 정보" active />
            <StageNav.Tab icon={ScrollText} label="본문 읽기" onClick={() => openReader(bookId)} />
            <StageNav.Tab icon={BarChart3} label="단어 분포" onClick={() => openWords(bookId)} />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
              <div style={{ maxWidth: 600, margin: '0 auto' }}>
                {/* SidePanel 재사용 — bookId 대상. onClose·canGoBack 미주입이라 X/뒤로 칩 없이 페이지 본문만.
                    onNodeLoaded 생략(책은 selectedNode가 아니므로 meta 오염 방지, SidePanel은 옵셔널 호출). */}
                <SidePanel
                  nodeId={bookId}
                  onSelectNode={selectNode}
                  verseLang={verseLang}
                  setVerseLang={setVerseLang}
                  explorePersonId={explorePersonId}
                  onExplorePerson={explorePerson}
                  curatedIds={curatedIds}
                  keyPeopleCards={keyPeopleCards}
                  onExploreJourney={selectPerson}
                  onOpenFamily={openFamily}
                />
                {/* 정경 순서 내비(task#211) — 끝 권은 해당 방향 버튼 미노출(창세기 이전·계시록 다음 없음) */}
                {booksOrder && (() => {
                  const idx = booksOrder.findIndex(b => b.id === bookId)
                  if (idx < 0) return null
                  const prevBook = idx > 0 ? booksOrder[idx - 1] : null
                  const nextBook = idx < booksOrder.length - 1 ? booksOrder[idx + 1] : null
                  const navBtn = {
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '8px 16px', borderRadius: 999, cursor: 'pointer',
                    border: '1px solid var(--line)', background: 'var(--bg-1)',
                    color: 'var(--ink)', fontSize: 13, fontFamily: 'var(--serif)',
                    transition: 'border-color var(--dur-fast)',
                  }
                  return (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 16px 28px' }}>
                      {prevBook ? (
                        <button onClick={() => openBook(prevBook.id)} style={navBtn}>← {prevBook.nameKo}</button>
                      ) : <span />}
                      {nextBook ? (
                        <button onClick={() => openBook(nextBook.id)} style={navBtn}>{nextBook.nameKo} →</button>
                      ) : <span />}
                    </div>
                  )
                })()}
              </div>
            </div>
          </div>
        </>
      )}

      {/* 가계도 단계 — 인물 상세 "가계도"에서 진입. 전용 전체화면 페이지(book과 동형, familyId 구동). */}
      {activeStage === 'family' && (
        <>
          <StageNav onBack={familyBack} backLabel="뒤로">
            {/* 인장 — 가계도 focus 인물(재중심화 시 key 리마운트로 1회 draw, 비큐레이션은 범용 폴백) */}
            <StageNav.Title
              icon={(
                <span key={familyId} style={{ color: 'var(--gold)', display: 'inline-flex' }}>
                  <PersonSymbol slug={getPersonSlug(familyId)} size={22} draw />
                </span>
              )}
              label="가계도"
            />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <FamilyTree
              key={familyId}
              personId={familyId}
              onRecenter={recenterFamily}
              onOpenPerson={(id) => selectPerson(id, 'intro')}
            />
          </div>
        </>
      )}

      {/* 단어 분포 단계 — 책 상세 "단어 분포"에서 진입. 전용 전체화면 페이지(family와 동형, wordsBookId 구동). */}
      {activeStage === 'words' && (
        <>
          {/* 책 정보 탭은 대상이 실제 책일 때만(성경 전체 'all'엔 책 상세가 없음) */}
          <StageNav onBack={wordsBack} backLabel="뒤로">
            {wordsBookId && wordsBookId !== 'all' && (
              <StageNav.Tab icon={BookOpen} label="책 정보" onClick={() => openBook(wordsBookId)} />
            )}
            <StageNav.Tab icon={BarChart3} label="단어 분포" active />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <WordDistributionView
              bookId={wordsBookId}
              onSelectBook={selectWordsBook}
              verseLang={verseLang}
              setVerseLang={setVerseLang}
            />
          </div>
        </>
      )}

      {/* 통계 단계 — 개요 "통계" 탭에서 진입. 전용 전체화면 페이지(family와 동형, 대상 id 없는 고정 뷰). */}
      {activeStage === 'stats' && (
        <>
          <StageNav onBack={statsBack} backLabel="뒤로">
            <StageNav.Title icon={<PieChart size={18} color="var(--gold)" />} label="성경 통계" />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <StatsView
              onSelectPerson={(id) => selectPerson(id, 'intro')}
              onSelectBook={openBook}
            />
          </div>
        </>
      )}

      {/* 주제 성구 단계 — 개요 "주제 성구" 탭에서 진입. 전용 전체화면 페이지(stats와 동형, 대상 id 없는 고정 뷰). */}
      {activeStage === 'topics' && (
        <>
          <StageNav onBack={topicsBack} backLabel="뒤로">
            <StageNav.Title icon={<Quote size={18} color="var(--gold)" />} label="주제 성구" />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <TopicalVersesView
              verseLang={verseLang}
              setVerseLang={setVerseLang}
            />
          </div>
        </>
      )}

      {/* 본문 리더 단계 — 책 상세 "본문 읽기"에서 진입. 전용 전체화면 페이지(words와 동형, readerBookId·readerChapter 구동). */}
      {activeStage === 'reader' && (
        <>
          <StageNav onBack={readerBack} backLabel="뒤로">
            <StageNav.Tab icon={BookOpen} label="책 정보" onClick={() => openBook(readerBookId)} />
            <StageNav.Tab icon={ScrollText} label="본문 읽기" active />
            <StageNav.Tab icon={BarChart3} label="단어 분포" onClick={() => openWords(readerBookId)} />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <ChapterReader
              bookId={readerBookId}
              chapter={readerChapter}
              onSelectChapter={n => { setHighlightVerseId(null); selectChapter(n) }}
              highlightVerseId={highlightVerseId}
              verseLang={verseLang}
              setVerseLang={setVerseLang}
              bookmarkEntry={bookmarkEntry}
              isBookmarked={isBookmarked}
              onToggleBookmark={toggleBookmark}
              onRecordRecent={recordRecent}
              isChapterRead={n => isRead(readerBookId, n)}
              onToggleRead={toggleRead}
              bookReadCount={bookReadCount}
            />
          </div>
        </>
      )}

      {/* 통사 연표 단계(task#271) — 전 성경을 한 연도 축에. 개요 내비 탭에서 진입 */}
      {activeStage === 'canon' && (
        <>
          <StageNav onBack={canonBack} backLabel="뒤로">
            <StageNav.Title icon={<CalendarRange size={18} color="var(--gold)" />} label="통사 연표" />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <CanonTimelineView
              onSelectNode={selectNode}
              onSelectPerson={(id) => selectPerson(id, 'intro')}
              isMobile={isMobile}
            />
          </div>
        </>
      )}

      {/* 장소 페이지 단계(task#270) — 지도 마커·정차지·상세 시트에서 진입하는 전용 전체화면 */}
      {activeStage === 'place' && (
        <>
          <StageNav onBack={placeBack} backLabel="뒤로">
            <StageNav.Title icon={<MapPin size={16} />} label="장소" />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <PlaceView
              placeId={placeId}
              onSelectPerson={(id) => selectPerson(id, 'intro')}
              onSelectNode={selectNode}
              verseLang={verseLang}
            />
          </div>
        </>
      )}

      {/* 테마 투어 목록 단계 — 허브에서 진입 */}
      {activeStage === 'tours' && (
        <>
          <StageNav onBack={backToHub} backLabel="인물 허브">
            <StageNav.Title icon={<span style={{ fontSize: 15 }}>🧭</span>} label="테마 투어" color={TYPE_COLOR.Book} gap={6} />
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <TourList onSelectTour={selectTour} />
          </div>
        </>
      )}

      {/* 탐험 단계 — 인물/투어 선택 후 지도·연표·관계·소개·의존 6뷰(ExploreStage) */}
      {activeStage === 'explore' && (
        <ExploreStage
          journey={journey}
          playback={playback}
          exploreView={exploreView}
          setExploreView={setExploreView}
          explorePersonId={explorePersonId}
          explorePersonName={explorePersonName}
          explorePersonSlug={explorePersonSlug}
          explorePersonEra={explorePersonEra}
          exploreTourId={exploreTourId}
          backToHub={backToHub}
          toursBack={toursBack}
          openFamily={openFamily}
          selectPerson={selectPerson}
          curatedIds={curatedIds}
          getPersonSlug={getPersonSlug}
          selectedNode={selectedNode}
          selectedNodeMeta={selectedNodeMeta}
          selectNode={selectNode}
          verseLang={verseLang}
          setVerseLang={setVerseLang}
          isMobile={isMobile}
          bookmarkEntry={bookmarkEntry}
          isBookmarked={isBookmarked}
          onToggleBookmark={toggleBookmark}
          onRecordRecent={recordRecent}
          onOpenPlace={openPlace}
        />
      )}

      {/* 상세 패널 — 탐험·개요 단계 공유 (허브엔 선택 없음 → 숨김). 데스크톱: 우측 슬라이드인 / 모바일: 하단 시트 */}
      {activeStage !== 'hub' && (
        <div
          data-node-sheet={selectedNode || undefined}
          data-node-sheet-open={sheetOpen ? 'true' : 'false'}
          style={{
            position: 'absolute', background: 'var(--bg-1)', overflowY: 'auto', zIndex: 10,
            transition: 'transform var(--dur-base) var(--ease-drawer)',
            ...(isMobile
              ? {
                  left: 0, right: 0, bottom: 0, height: `${SHEET_VH}vh`,
                  boxShadow: 'var(--shadow-2)',
                  // 인물 선택 시 자동 선택된 인물 자신의 상세는 모바일에서 시트로 띄우지 않는다 —
                  // 여정 칩 스트립을 가려 "첫 로딩 시 여정이 안 보이는" 문제가 되기 때문.
                  // (SidePanel은 DOM에 남아 인물 이름은 그대로 로드됨. personEventIds는 explorePersonId 구동.) 장소 등 다른 노드 선택 시에는 정상 표시.
                  transform: sheetOpen ? 'translateY(0)' : 'translateY(100%)',
                }
              : {
                  top: HEADER_H + RIBBON_OVERHANG + NAV_H, right: 0, bottom: 0, width: 360,
                  boxShadow: 'var(--shadow-2)',
                  // 관계·하나님 의존 뷰는 전용 전체화면 — 탐험 인물 자신의 상세 시트로 우측을 덮지 않는다(다른 뷰로 토글 시 복귀).
                  // 탐험 인물 자신의 상세는 어느 뷰에서도 시트로 띄우지 않는다(모바일 sheetOpen과 동일 규약, task#263 — 이전엔 intro 뷰에만 한정돼 map 등 다른 뷰 진입 시 자기시트가 새 노출됐다).
                  transform: selectedNode && exploreView !== 'relations' && exploreView !== 'reliance' && selectedNode !== explorePersonId ? 'translateX(0)' : 'translateX(100%)',
                }),
          }}
          onTouchStart={isMobile ? onSheetTouchStart : undefined}
          onTouchEnd={isMobile ? onSheetTouchEnd : undefined}
        >
          {isMobile && (
            <div style={{
              position: 'sticky', top: 0, zIndex: 3,
              display: 'flex', justifyContent: 'center', padding: '8px 0 4px',
              background: 'var(--bg-1)',
            }}>
              <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--ink-faint)' }} />
            </div>
          )}
          <SidePanel
            nodeId={selectedNode}
            onSelectNode={selectNode}
            onBack={goBack}
            canGoBack={history.length > 0}
            onNodeLoaded={onNodeLoaded}
            verseLang={verseLang}
            setVerseLang={setVerseLang}
            explorePersonId={explorePersonId}
            onExplorePerson={explorePerson}
            curatedIds={curatedIds}
            keyPeopleCards={keyPeopleCards}
            onExploreJourney={selectPerson}
            onOpenFamily={openFamily}
            onOpenPlace={openPlace}
            onClose={() => window.history.back()}
            stickyTop={isMobile ? 16 : 0}
          />
        </div>
      )}

      {/* 통합 검색 오버레이(task#267) — 전 스테이지 위. `/` 또는 헤더 검색 버튼으로 열린다 */}
      {searchOpen && (
        <SearchPanel
          isMobile={isMobile}
          onClose={() => setSearchOpen(false)}
          onSelectNode={handleSearchNode}
          onSelectVerse={handleSearchVerse}
        />
      )}

    </div>
  )
}

export default App
