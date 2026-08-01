import { useState, useEffect, useRef } from 'react'
import { BookOpen, BarChart3, ScrollText, PieChart, Quote } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import SidePanel from './SidePanel'
import BibleOverviewView from './BibleOverviewView'
import PersonHub from './PersonHub'
import IntroView from './IntroView'
import SpineHeader, { HEADER_H, RIBBON_OVERHANG } from './SpineHeader'
import StageNav, { NAV_H } from './StageNav'
import ExploreStage from './ExploreStage'
import { useExploreJourney } from './useExploreJourney'
import PersonSymbol from './personSymbols'
import FamilyTree from './FamilyTree'
import WordDistributionView from './WordDistributionView'
import StatsView from './StatsView'
import TopicalVersesView from './TopicalVersesView'
import ChapterReader from './ChapterReader'
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
    activeStage, exploreView, explorePersonId, explorePersonName, explorePersonSlug, explorePersonEra, exploreTourId, bookId, familyId, wordsBookId, readerBookId, readerChapter, curatedIds, keyPeopleCards, sheetOpen,
    setExploreView, selectPerson, explorePerson, backToHub, openIntro, openOverview, overviewBack,
    openTours, selectTour, toursBack, openBook, bookBack, openFamily, recenterFamily, familyBack,
    openWords, selectWordsBook, wordsBack, openReader, selectChapter, readerBack, openStats, statsBack, openTopics, topicsBack, onNodeLoaded, getPersonSlug,
  } = useStageNavigation({ selectedNode, selectNodeFresh, closePanel, handleNodeLoaded })

  // 여정 데이터 상태 — 코드는 useExploreJourney, **수명은 App**(족보 스테이지 진입 시 ExploreStage가
  // 언마운트되므로 여기서 소유해야 복귀 시 재fetch·정차지 초기화가 없다. 훅 상단 주석 참조).
  const journey = useExploreJourney({ explorePersonId, exploreTourId })

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
      : activeStage === 'overview' || activeStage === 'book' || activeStage === 'words' || activeStage === 'reader' || activeStage === 'stats' || activeStage === 'topics' ? 'books'
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
          <PersonHub onSelectPerson={(id) => selectPerson(id, 'intro')} />
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
          </StageNav>
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <BibleOverviewView
              onSelectNode={openBook}
              selectedNode={bookId}
              verseLang={verseLang}
              setVerseLang={setVerseLang}
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
              onSelectChapter={selectChapter}
              verseLang={verseLang}
              setVerseLang={setVerseLang}
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
        />
      )}

      {/* 상세 패널 — 탐험·개요 단계 공유 (허브엔 선택 없음 → 숨김). 데스크톱: 우측 슬라이드인 / 모바일: 하단 시트 */}
      {activeStage !== 'hub' && (
        <div
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
                  // 소개 뷰는 자기 자신이 본문이라 자기 시트만 억제(다른 노드 선택 시에는 정상 표시).
                  transform: selectedNode && exploreView !== 'relations' && exploreView !== 'reliance' && !(exploreView === 'intro' && selectedNode === explorePersonId) ? 'translateX(0)' : 'translateX(100%)',
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
            onClose={() => window.history.back()}
            stickyTop={isMobile ? 16 : 0}
          />
        </div>
      )}

    </div>
  )
}

export default App
