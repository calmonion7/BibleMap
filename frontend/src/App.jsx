import { useState, useEffect, useRef, useMemo } from 'react'
import { Map, Clock, BookOpen, Users, UserRound } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import RelationsView from './RelationsView'
import BibleOverviewView from './BibleOverviewView'
import PersonHub from './PersonHub'
import TourList from './TourList'
import JourneyList from './JourneyList'
import { MOBILE_BREAKPOINT, SHEET_VH, JOURNEY_SHEET_VH } from './constants'
import { useNodeSelection } from './useNodeSelection'
import { useStageNavigation } from './useStageNavigation'
import { apiGet } from './api'

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT}px)`

// 탐험 토글 정의
const EXPLORE_TABS = [
  { key: 'map', icon: Map, label: '지도' },
  { key: 'timeline', icon: Clock, label: '타임라인' },
]

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
    activeStage, exploreView, explorePersonId, explorePersonName, exploreTourId, curatedIds, sheetOpen,
    setExploreView, selectPerson, explorePerson, backToHub, openOverview, overviewBack,
    openTours, selectTour, toursBack, onNodeLoaded,
  } = useStageNavigation({ selectedNode, selectNodeFresh, closePanel, handleNodeLoaded })

  // 여정 데이터 — 인물/투어 선택 시 한 번 fetch, MapView·JourneyList 공유
  const [journeyStops, setJourneyStops] = useState(null)
  // 탐험 중 투어의 제목 — /tour 응답에서 채움(내비 헤더·JourneyList·타임라인 라벨용)
  const [exploreTourName, setExploreTourName] = useState(null)
  // 투어 타임라인 필터 — TimelineView가 Set.has()로 쓰므로 Set으로, 참조 안정화(인물의 personEventIds와 동일 형태)
  const tourEventIds = useMemo(
    () => (exploreTourId && journeyStops ? new Set(journeyStops.map(s => s.eventId)) : null),
    [exploreTourId, journeyStops],
  )
  // 인물 타임라인 필터 — explorePersonId 구동(선택 노드와 무관, tourEventIds와 대칭). 헌트 #10:
  // 노드 클릭에 소실되지 않도록 selectedNode가 아닌 탐험 인물에 묶는다.
  const [personEventIds, setPersonEventIds] = useState(null)
  useEffect(() => {
    let cancelled = false
    if (explorePersonId) {
      apiGet(`/person/${explorePersonId}/event-ids`)
        .then(data => { if (!cancelled) setPersonEventIds(new Set(data.eventIds)) })
        .catch(e => { if (!cancelled) { console.warn('[App] 인물 사건 목록 로드 실패', e); setPersonEventIds(null) } })
    } else {
      Promise.resolve().then(() => { if (!cancelled) setPersonEventIds(null) })
    }
    return () => { cancelled = true }
  }, [explorePersonId])
  const [activeStopIdx, setActiveStopIdx] = useState(null)
  // 모바일 여정 "읽기 모드" — 펼친 사건 id. App이 소유해 오버레이 높이 전환·바깥 탭 닫기를 제어한다.
  const [readingEventId, setReadingEventId] = useState(null)
  const [reduceMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)

  useEffect(() => {
    const ctrl = new AbortController()
    if (explorePersonId) {
      apiGet(`/person/${explorePersonId}/journey`, { signal: ctrl.signal })
        .then(({ stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setReadingEventId(null); setExploreTourName(null) }) // async 콜백 — v7 OK
        .catch((e) => { if (e?.name !== 'AbortError') { console.warn('[App] 인물 여정 로드 실패', e); setJourneyStops([]) } })
    } else if (exploreTourId) {
      apiGet(`/tour/${exploreTourId}`, { signal: ctrl.signal })
        .then(({ title, stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setReadingEventId(null); setExploreTourName(title) })
        .catch((e) => { if (e?.name !== 'AbortError') { console.warn('[App] 투어 로드 실패', e); setJourneyStops([]) } })
    } else {
      // 인물·투어 모두 미선택 → 비동기로 초기화(effect 동기 setState 금지 규칙 회피)
      Promise.resolve().then(() => { setJourneyStops(null); setActiveStopIdx(null); setReadingEventId(null); setExploreTourName(null) })
    }
    return () => ctrl.abort()
  }, [explorePersonId, exploreTourId])

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

  const NAV_H = 48

  // 탐험 단계 내비게이션 바
  function renderExploreNav() {
    const isTour = exploreTourId != null
    const headingName = isTour ? exploreTourName : explorePersonName
    const backLabel = isTour ? '테마 목록' : '다른 인물'
    const onBack = isTour ? toursBack : backToHub
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)', borderBottom: 'none',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        {/* 복귀 — 투어면 "투어명 + 테마 목록", 인물이면 "인물명 + 다른 인물" */}
        <button
          onClick={onBack}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '0 14px', height: '100%',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--ink-dim)',
            borderRight: '1px solid var(--line)',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 13 }}>←</span>
          {headingName ? (
            <span style={{ fontSize: 13, fontFamily: isTour ? undefined : 'var(--serif)', color: isTour ? TYPE_COLOR.Book : 'var(--gold)', fontWeight: 600, maxWidth: isMobile ? 80 : 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {headingName}
            </span>
          ) : null}
          <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{backLabel}</span>
        </button>

        {/* 지도 / 타임라인 / 관계(인물 모드 한정) 토글 */}
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          {[...EXPLORE_TABS, ...(explorePersonId && !exploreTourId ? [{ key: 'relations', icon: Users, label: '관계' }, { key: 'intro', icon: UserRound, label: '소개' }] : [])].map(tab => {
            const Icon = tab.icon
            const active = exploreView === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setExploreView(tab.key)}
                style={{
                  padding: '0 14px', height: '100%',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
                  color: active ? 'var(--ink)' : 'var(--ink-faint)',
                  borderBottom: active ? '2px solid var(--gold)' : '2px solid transparent',
                  border: 'none', background: 'none', cursor: 'pointer',
                  transition: 'color 0.15s',
                }}
              >
                <Icon size={18} />
                <span style={{ fontSize: 10, lineHeight: 1 }}>{tab.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  // 개요 단계 내비게이션 바
  function renderOverviewNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        <button
          onClick={overviewBack}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '0 14px', height: '100%',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--ink-dim)',
            borderRight: '1px solid var(--line)',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 13 }}>←</span>
          <span style={{ fontSize: 13 }}>인물 허브</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 14px', gap: 6 }}>
          <BookOpen size={18} color="var(--ink-faint)" />
          <span style={{ color: 'var(--ink-dim)', fontSize: 13 }}>성경 책 둘러보기</span>
        </div>
      </div>
    )
  }

  // 투어 목록 단계 내비게이션 바
  function renderToursNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        <button
          onClick={backToHub}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '0 14px', height: '100%',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--ink-dim)',
            borderRight: '1px solid var(--line)',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 13 }}>←</span>
          <span style={{ fontSize: 13 }}>인물 허브</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 14px', gap: 6 }}>
          <span style={{ fontSize: 15 }}>🧭</span>
          <span style={{ color: 'var(--ink-dim)', fontSize: 13 }}>테마 투어</span>
        </div>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100dvh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

      {/* 허브 단계 — 인물 선택 전 */}
      {activeStage === 'hub' && (
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <PersonHub
            onSelectPerson={selectPerson}
            onOpenOverview={openOverview}
            onOpenTours={openTours}
          />
        </div>
      )}

      {/* 개요 단계 — 허브에서 진입 */}
      {activeStage === 'overview' && (
        <>
          {renderOverviewNav()}
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <BibleOverviewView
              onSelectNode={selectNode}
              selectedNode={selectedNode}
            />
          </div>
        </>
      )}

      {/* 테마 투어 목록 단계 — 허브에서 진입 */}
      {activeStage === 'tours' && (
        <>
          {renderToursNav()}
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <TourList onSelectTour={selectTour} />
          </div>
        </>
      )}

      {/* 탐험 단계 — 인물/투어 선택 후 지도·타임라인 */}
      {activeStage === 'explore' && (
        <>
          {renderExploreNav()}

          {/* 전체화면 뷰 — 항상 마운트, CSS 토글로 상태 보존 */}
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <div style={{ display: exploreView === 'map' ? 'flex' : 'none', height: '100%' }}>
              {/* 여정 사이드 리스트 — 데스크톱: 좌측 200px 고정 / 모바일: 숨김(지도 위에 하단 미니시트) */}
              {!isMobile && journeyStops && journeyStops.length > 0 && (
                <div style={{ width: 290, flexShrink: 0, overflow: 'hidden' }}>
                  <JourneyList
                    stops={journeyStops}
                    activeStopIdx={activeStopIdx}
                    onStopSelect={setActiveStopIdx}
                    verseLang={verseLang}
                    setVerseLang={setVerseLang}
                    personName={exploreTourId ? null : explorePersonName}
                    tourName={exploreTourId ? exploreTourName : null}
                  />
                </div>
              )}
              <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
                <MapView
                  onSelectNode={selectNode}
                  selectedNode={selectedNode}
                  personId={explorePersonId}
                  isVisible={exploreView === 'map'}
                  journeyStops={journeyStops}
                  activeStopIdx={activeStopIdx}
                  onStopSelect={setActiveStopIdx}
                />
                {/* 모바일 여정 — 하단 세로 아코디언(데스크톱과 동일 JourneyList 재사용). 📖 탭 시 ~90dvh 읽기 모드로 확장. */}
                {isMobile && journeyStops && journeyStops.length > 0 && (
                  <>
                    {/* 읽는 중 노출된 상단 지도 영역 탭 → 읽기 모드 닫기(장소 SidePanel 시트와 겹침 회피) */}
                    {readingEventId && (
                      <div
                        onClick={() => setReadingEventId(null)}
                        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: '90dvh', zIndex: 4 }}
                      />
                    )}
                    <div style={{
                      position: 'absolute', bottom: 0, left: 0, right: 0,
                      height: readingEventId ? '90dvh' : `${JOURNEY_SHEET_VH}dvh`, zIndex: 5,
                      transition: reduceMotion ? undefined : 'height 0.25s ease',
                      borderTop: '1px solid var(--line-strong)',
                      boxShadow: 'var(--shadow-2)',
                    }}>
                      <JourneyList
                        stops={journeyStops}
                        activeStopIdx={activeStopIdx}
                        onStopSelect={setActiveStopIdx}
                        verseLang={verseLang}
                        setVerseLang={setVerseLang}
                        personName={exploreTourId ? null : explorePersonName}
                        tourName={exploreTourId ? exploreTourName : null}
                        readingEventId={readingEventId}
                        onReadingChange={setReadingEventId}
                      />
                    </div>
                  </>
                )}
              </div>
            </div>
            <div style={{ display: exploreView === 'timeline' ? 'block' : 'none', height: '100%' }}>
              <TimelineView
                onSelectNode={selectNode}
                selectedNode={selectedNode}
                bookFilter={selectedNodeMeta?.label === 'Book' ? selectedNodeMeta : null}
                personFilter={explorePersonId != null ? personEventIds : tourEventIds}
                personName={exploreTourId != null ? exploreTourName : explorePersonName}
                verseLang={verseLang}
                setVerseLang={setVerseLang}
              />
            </div>
            {/* 관계 뷰 — 인물 모드 전용(레인 개요 + 초점 쌍 + 근거 구절 레이어) */}
            {exploreView === 'relations' && explorePersonId && (
              <div style={{ height: '100%' }}>
                <RelationsView
                  key={explorePersonId}
                  personId={explorePersonId}
                  personName={explorePersonName}
                  verseLang={verseLang}
                  setVerseLang={setVerseLang}
                  curatedIds={curatedIds}
                  onExploreJourney={selectPerson}
                />
              </div>
            )}
            {/* 인물 소개 뷰 — 지도·타임라인·관계와 같은 레벨의 페이지(SidePanel 재사용, 인물 모드 전용).
                탐험 자기 시트 억제 규칙(sheetOpen ≠ explorePersonId)은 무접촉 — 전용 뷰라 시트가 아니다. */}
            {exploreView === 'intro' && explorePersonId && (
              <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
                <div style={{ maxWidth: 560, margin: '0 auto', padding: '4px 0 48px' }}>
                  <SidePanel
                    key={explorePersonId}
                    nodeId={explorePersonId}
                    onSelectNode={selectNode}
                    verseLang={verseLang}
                    setVerseLang={setVerseLang}
                    explorePersonId={explorePersonId}
                    onExplorePerson={explorePerson}
                    curatedIds={curatedIds}
                    onExploreJourney={selectPerson}
                  />
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* 상세 패널 — 탐험·개요 단계 공유 (허브엔 선택 없음 → 숨김). 데스크톱: 우측 슬라이드인 / 모바일: 하단 시트 */}
      {activeStage !== 'hub' && (
        <div
          style={{
            position: 'absolute', background: 'var(--bg-1)', overflowY: 'auto', zIndex: 10,
            transition: 'transform 0.25s ease',
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
                  top: NAV_H, right: 0, bottom: 0, width: 360,
                  boxShadow: 'var(--shadow-2)',
                  // 관계 뷰는 전용 전체화면 — 탐험 인물 자신의 상세 시트로 우측을 덮지 않는다(다른 뷰로 토글 시 복귀).
                  // 소개 뷰는 자기 자신이 본문이라 자기 시트만 억제(다른 노드 선택 시에는 정상 표시).
                  transform: selectedNode && exploreView !== 'relations' && !(exploreView === 'intro' && selectedNode === explorePersonId) ? 'translateX(0)' : 'translateX(100%)',
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
            onExploreJourney={selectPerson}
            onClose={() => window.history.back()}
            stickyTop={isMobile ? 16 : 0}
          />
        </div>
      )}

    </div>
  )
}

export default App
