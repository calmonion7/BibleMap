import { useState, useEffect, useRef, useCallback } from 'react'
import { Map, Clock, BookOpen } from 'lucide-react'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import BibleOverviewView from './BibleOverviewView'
import PersonHub from './PersonHub'
import JourneyList from './JourneyList'
import { MOBILE_BREAKPOINT, SHEET_VH } from './constants'
import { useNodeSelection } from './useNodeSelection'
import { apiGet } from './api'

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT}px)`

// 탐험 토글 정의
const EXPLORE_TABS = [
  { key: 'map', icon: Map, label: '지도' },
  { key: 'timeline', icon: Clock, label: '타임라인' },
]

function App() {
  // 'hub' | 'explore' | 'overview'
  const [activeStage, setActiveStage] = useState('hub')
  // 탐험 내 토글: 'map' | 'timeline'
  const [exploreView, setExploreView] = useState('map')
  // 절 본문 표시 언어('ko'|'en', 기본 ko) — 타임라인·SidePanel 공유.
  const [verseLang, setVerseLang] = useState('ko')
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)

  const {
    selectedNode, selectedNodeMeta, history, personEventIds,
    handleNodeLoaded, selectNode, selectNodeFresh, goBack, closePanel,
  } = useNodeSelection()

  // 탐험 중인 인물 — selectedNode와 분리해 장소 클릭 시에도 여정·맵 장소 기준 유지
  const [explorePersonId, setExplorePersonId] = useState(null)
  const [explorePersonName, setExplorePersonName] = useState(null)

  // 큐레이션 인물 id 집합 — SidePanel '여정 탐험' CTA 노출 판단용(1회 fetch)
  const [curatedIds, setCuratedIds] = useState(null)
  useEffect(() => {
    apiGet('/persons/curated')
      .then(list => setCuratedIds(new Set(list.map(p => p.id))))
      .catch(() => {})
  }, [])

  // 여정 데이터 — 인물 선택 시 한 번 fetch, MapView·JourneyList 공유
  const [journeyStops, setJourneyStops] = useState(null)
  const [activeStopIdx, setActiveStopIdx] = useState(null)
  // 모바일 여정 "읽기 모드" — 펼친 사건 id. App이 소유해 오버레이 높이 전환·바깥 탭 닫기를 제어한다.
  const [readingEventId, setReadingEventId] = useState(null)
  const [reduceMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)

  useEffect(() => {
    const ctrl = new AbortController()
    if (!explorePersonId) {
      // 인물 미선택 → 비동기로 초기화(effect 동기 setState 금지 규칙 회피)
      Promise.resolve().then(() => { setJourneyStops(null); setActiveStopIdx(null); setReadingEventId(null) })
      return () => ctrl.abort()
    }
    apiGet(`/person/${explorePersonId}/journey`, { signal: ctrl.signal })
      .then(({ stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setReadingEventId(null) }) // async 콜백 — v7 OK
      .catch((e) => { if (e?.name !== 'AbortError') setJourneyStops([]) })
    return () => ctrl.abort()
  }, [explorePersonId])

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // 허브에서 인물 카드 클릭 — 탐험으로 전환
  function handleSelectPerson(id) {
    selectNodeFresh(id)
    setExplorePersonId(id)
    setActiveStage('explore')
  }

  // SidePanel에서 "이 곳을 지난 다른 인물" 칩 클릭 — 같은 탐험 단계에서 인물 전환
  function handleExplorePerson(id) {
    setExplorePersonId(id)
    selectNodeFresh(id)
  }

  // SidePanel onNodeLoaded — 참조 안정화(useCallback). 인라인 화살표면 매 렌더 새 ref가 되어
  // SidePanel의 /node fetch effect(deps에 onNodeLoaded)가 매번 재실행→setCollapsed({}) 리셋으로
  // 섹션이 안 펼쳐지는 버그가 난다. explorePersonId 변경 시에만 갱신.
  const handleSidePanelNodeLoaded = useCallback((data) => {
    handleNodeLoaded(data)
    if (data.label === 'Person' && data.id === explorePersonId) setExplorePersonName(data.nameKo)
  }, [handleNodeLoaded, explorePersonId])

  // 탐험에서 "다른 인물" 클릭 — 허브로 복귀, 선택 해제
  function handleBackToHub() {
    closePanel()
    setExplorePersonId(null)
    setExplorePersonName(null)
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
    if (dy > 80 && sheetAtTop.current) closePanel()
    swipeStartY.current = null
  }

  const NAV_H = 48

  // 탐험 단계 내비게이션 바
  function renderExploreNav() {
    const personName = explorePersonName
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: '#1a1a2e', borderBottom: 'none',
        zIndex: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        gap: 0,
      }}>
        {/* 허브 복귀 — "현재 인물명 + 다른 인물" */}
        <button
          onClick={handleBackToHub}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '0 14px', height: '100%',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'rgba(255,255,255,0.7)',
            borderRight: '1px solid rgba(255,255,255,0.1)',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 13 }}>←</span>
          {personName ? (
            <span style={{ fontSize: 13, color: '#c9a84c', fontWeight: 600, maxWidth: isMobile ? 80 : 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {personName}
            </span>
          ) : null}
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)' }}>다른 인물</span>
        </button>

        {/* 지도 / 타임라인 토글 */}
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          {EXPLORE_TABS.map(tab => {
            const Icon = tab.icon
            const active = exploreView === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setExploreView(tab.key)}
                style={{
                  padding: '0 14px', height: '100%',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
                  color: active ? 'white' : 'rgba(255,255,255,0.5)',
                  borderBottom: active ? '2px solid #7c9cfc' : '2px solid transparent',
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
        background: '#1a1a2e',
        zIndex: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        gap: 0,
      }}>
        <button
          onClick={handleOverviewBack}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '0 14px', height: '100%',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'rgba(255,255,255,0.7)',
            borderRight: '1px solid rgba(255,255,255,0.1)',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 13 }}>←</span>
          <span style={{ fontSize: 13 }}>인물 허브</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 14px', gap: 6 }}>
          <BookOpen size={18} color="rgba(255,255,255,0.5)" />
          <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>성경 책 둘러보기</span>
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
            onSelectPerson={handleSelectPerson}
            onOpenOverview={handleOpenOverview}
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

      {/* 탐험 단계 — 인물 선택 후 지도·타임라인 */}
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
                    personName={explorePersonName}
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
                      height: readingEventId ? '90dvh' : '42dvh', zIndex: 5,
                      transition: reduceMotion ? undefined : 'height 0.25s ease',
                      borderTop: '1px solid rgba(255,255,255,0.12)',
                      boxShadow: '0 -3px 12px rgba(0,0,0,0.3)',
                    }}>
                      <JourneyList
                        stops={journeyStops}
                        activeStopIdx={activeStopIdx}
                        onStopSelect={setActiveStopIdx}
                        verseLang={verseLang}
                        setVerseLang={setVerseLang}
                        personName={explorePersonName}
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
                personFilter={explorePersonId != null ? personEventIds : null}
                personName={explorePersonName}
                verseLang={verseLang}
                setVerseLang={setVerseLang}
              />
            </div>
          </div>
        </>
      )}

      {/* 상세 패널 — 탐험·개요 단계 공유 (허브엔 선택 없음 → 숨김). 데스크톱: 우측 슬라이드인 / 모바일: 하단 시트 */}
      {activeStage !== 'hub' && (
        <div
          style={{
            position: 'absolute', background: 'white', overflowY: 'auto', zIndex: 10,
            transition: 'transform 0.25s ease',
            ...(isMobile
              ? {
                  left: 0, right: 0, bottom: 0, height: `${SHEET_VH}vh`,
                  boxShadow: '0 -3px 12px rgba(0,0,0,0.15)',
                  // 인물 선택 시 자동 선택된 인물 자신의 상세는 모바일에서 시트로 띄우지 않는다 —
                  // 여정 칩 스트립을 가려 "첫 로딩 시 여정이 안 보이는" 문제가 되기 때문.
                  // (SidePanel은 DOM에 남아 personEventIds·이름은 그대로 로드됨.) 장소 등 다른 노드 선택 시에는 정상 표시.
                  transform: (selectedNode && selectedNode !== explorePersonId) ? 'translateY(0)' : 'translateY(100%)',
                }
              : {
                  top: NAV_H, right: 0, bottom: 0, width: 360,
                  boxShadow: '-3px 0 12px rgba(0,0,0,0.15)',
                  transform: selectedNode ? 'translateX(0)' : 'translateX(100%)',
                }),
          }}
          onTouchStart={isMobile ? onSheetTouchStart : undefined}
          onTouchEnd={isMobile ? onSheetTouchEnd : undefined}
        >
          {isMobile && (
            <div style={{
              position: 'sticky', top: 0, zIndex: 3,
              display: 'flex', justifyContent: 'center', padding: '8px 0 4px',
              background: 'white',
            }}>
              <div style={{ width: 36, height: 4, borderRadius: 2, background: '#ddd' }} />
            </div>
          )}
          <button
            onClick={closePanel}
            style={{
              position: 'absolute', top: 8, right: 8, zIndex: 2,
              width: 44, height: 44, borderRadius: '50%',
              border: '1px solid #ddd', background: 'white',
              cursor: 'pointer', fontSize: 16, lineHeight: 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >×</button>
          <SidePanel
            nodeId={selectedNode}
            onSelectNode={selectNode}
            onBack={goBack}
            canGoBack={history.length > 0}
            onNodeLoaded={handleSidePanelNodeLoaded}
            verseLang={verseLang}
            setVerseLang={setVerseLang}
            explorePersonId={explorePersonId}
            onExplorePerson={handleExplorePerson}
            curatedIds={curatedIds}
            onExploreJourney={handleSelectPerson}
          />
        </div>
      )}

    </div>
  )
}

export default App
