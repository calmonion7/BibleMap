import { useState, useEffect, useRef, useMemo } from 'react'
import { Route, Clock, BookOpen, Users, UserRound, Network, BarChart3, HeartHandshake, ScrollText } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import RelationsView from './RelationsView'
import BibleOverviewView from './BibleOverviewView'
import PersonHub from './PersonHub'
import PersonIntro from './PersonIntro'
import SpineHeader, { HEADER_H } from './SpineHeader'
import PersonSymbol from './personSymbols'
import FamilyTree from './FamilyTree'
import WordDistributionView from './WordDistributionView'
import ChapterReader from './ChapterReader'
import RelianceView from './RelianceView'
import TourList from './TourList'
import JourneyList from './JourneyList'
import { MOBILE_BREAKPOINT, SHEET_VH, JOURNEY_SHEET_VH } from './constants'
import { useNodeSelection } from './useNodeSelection'
import { useStageNavigation } from './useStageNavigation'
import { apiGet } from './api'

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT}px)`

// 탐험 토글 정의 — 지도 라벨은 "여정"(인물이 지도 위에 남긴 이동 경로)
const EXPLORE_TABS = [
  { key: 'map', icon: Route, label: '여정' },
  { key: 'timeline', icon: Clock, label: '연표' },  // '타임라인'은 모바일 6탭 폭에서 2줄 — 2글자로 축약
]
const INTRO_TAB = { key: 'intro', icon: UserRound, label: '소개' }
const RELATIONS_TAB = { key: 'relations', icon: Users, label: '관계' }
// 하나님 의존 — 관계와 동형 탭(setExploreView). 그 인물의 하나님 의존도·궤적.
// 라벨은 짧게 '의존'(모바일 6탭 폭에서 '하나님 의존'은 3줄로 감김) — 아이콘·본문 헤더가 맥락 전달.
const RELIANCE_TAB = { key: 'reliance', icon: HeartHandshake, label: '의존' }
// 가계도 — 탭 전환(setExploreView)이 아니라 전용 스테이지(openFamily) 진입. 관계 옆에 배치.
// 라벨 '족보'(2글자) — '가계도'는 모바일 6탭 폭에서 2줄로 감김.
const FAMILY_TAB = { key: 'family', icon: Network, label: '족보' }

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
    activeStage, exploreView, explorePersonId, explorePersonName, explorePersonSlug, exploreTourId, bookId, familyId, wordsBookId, readerBookId, readerChapter, curatedIds, keyPeopleCards, sheetOpen,
    setExploreView, selectPerson, explorePerson, backToHub, openOverview, overviewBack,
    openTours, selectTour, toursBack, openBook, bookBack, openFamily, recenterFamily, familyBack,
    openWords, selectWordsBook, wordsBack, openReader, selectChapter, readerBack, onNodeLoaded, getPersonSlug,
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
  // 무좌표 여정(task#201) — 정차 전부가 지도 좌표 없음(셋·아벨·에녹) → 지도 대신 전면 리스트
  const journeyMapless = !!(journeyStops && journeyStops.length > 0 && !journeyStops.some(s => s.lng != null && s.lat != null))
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

  useEffect(() => {
    const ctrl = new AbortController()
    if (explorePersonId) {
      apiGet(`/person/${explorePersonId}/journey`, { signal: ctrl.signal })
        .then(({ stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setExploreTourName(null) }) // async 콜백 — v7 OK
        .catch((e) => { if (e?.name !== 'AbortError') { console.warn('[App] 인물 여정 로드 실패', e); setJourneyStops([]) } })
    } else if (exploreTourId) {
      apiGet(`/tour/${exploreTourId}`, { signal: ctrl.signal })
        .then(({ title, stops }) => { setJourneyStops(stops); setActiveStopIdx(null); setExploreTourName(title) })
        .catch((e) => { if (e?.name !== 'AbortError') { console.warn('[App] 투어 로드 실패', e); setJourneyStops([]) } })
    } else {
      // 인물·투어 모두 미선택 → 비동기로 초기화(effect 동기 setState 금지 규칙 회피)
      Promise.resolve().then(() => { setJourneyStops(null); setActiveStopIdx(null); setExploreTourName(null) })
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
    activeStage === 'overview' || activeStage === 'book' || activeStage === 'words' || activeStage === 'reader' ? 'books'
      : activeStage === 'tours' || (activeStage === 'explore' && exploreTourId != null) ? 'tours'
        : 'persons'

  // 리본 클릭 — 기존 내비 콜백 조합만(상태 머신·URL 무변경). 탐험 중 열린 시트가 새 부로 넘어오지 않게 closePanel 동반.
  function handleSelectSection(key) {
    if (key === 'persons') backToHub()
    else if (key === 'books') { closePanel(); openOverview() }
    else { closePanel(); openTours() }
  }

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
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
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
          {/* 인장 — 탐험 중 인물의 상징물(인물 전환 시에만 key 리마운트로 1회 draw, 탭 전환엔 정적) */}
          {!isTour && explorePersonId && (
            <span key={explorePersonId} style={{ color: 'var(--gold)', flexShrink: 0, display: 'inline-flex' }}>
              <PersonSymbol slug={getPersonSlug(explorePersonId)} size={isMobile ? 20 : 26} draw />
            </span>
          )}
          {headingName ? (
            <span style={{ fontSize: 13, fontFamily: 'var(--serif)', color: isTour ? TYPE_COLOR.Book : 'var(--gold)', fontWeight: 600, maxWidth: isMobile ? 80 : 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {headingName}
            </span>
          ) : null}
          {/* 모바일 인물 모드는 보조 라벨 생략 — 인장이 차지한 폭을 회수해 6탭(족보까지)이 뷰포트 안에 들게 */}
          {!(isMobile && !isTour) && <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{backLabel}</span>}
        </button>

        {/* 지도 / 타임라인 / 관계(인물 모드 한정) 토글 */}
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          {/* 인물 모드: 소개(맨앞) · 여정길 · 타임라인 · 관계 / 투어 모드: 여정길 · 타임라인 */}
          {(explorePersonId && !exploreTourId ? [INTRO_TAB, ...EXPLORE_TABS, RELATIONS_TAB, RELIANCE_TAB, FAMILY_TAB] : EXPLORE_TABS).map(tab => {
            const Icon = tab.icon
            const active = exploreView === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => tab.key === 'family' ? openFamily(explorePersonId) : setExploreView(tab.key)}
                style={{
                  padding: '0 14px', height: '100%',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
                  color: active ? 'var(--ink)' : 'var(--ink-faint)',
                  borderBottom: active ? '2px solid var(--gold)' : '2px solid transparent',
                  border: 'none', background: 'none', cursor: 'pointer',
                  transition: 'color var(--dur-fast), border-color var(--dur-fast)',
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

  // 개요 단계 내비게이션 바 — 하위 메뉴 탭(책 둘러보기 · 단어 분포), 탐험 뷰 토글과 동형
  function renderOverviewNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
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
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <button
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink)',
              borderBottom: '2px solid var(--gold)',
              border: 'none', background: 'none', cursor: 'default',
            }}
          >
            <BookOpen size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>책 둘러보기</span>
          </button>
          <button
            onClick={() => openWords('all')}
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink-faint)',
              border: 'none', background: 'none', cursor: 'pointer',
              transition: 'color var(--dur-fast), border-color var(--dur-fast)',
            }}
          >
            <BarChart3 size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>단어 분포</span>
          </button>
        </div>
      </div>
    )
  }

  // 책 상세 단계 내비게이션 바 — 개요(성경 책 둘러보기)로 복귀 + 하위 메뉴 탭(책 정보 · 단어 분포, 둘러보기 내비와 동형)
  function renderBookNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        <button
          onClick={bookBack}
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
          <span style={{ fontSize: 13 }}>성경 책 둘러보기</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <button
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink)',
              borderBottom: '2px solid var(--gold)',
              border: 'none', background: 'none', cursor: 'default',
            }}
          >
            <BookOpen size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>책 정보</span>
          </button>
          <button
            onClick={() => openReader(bookId)}
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink-faint)',
              border: 'none', background: 'none', cursor: 'pointer',
              transition: 'color var(--dur-fast), border-color var(--dur-fast)',
            }}
          >
            <ScrollText size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>본문 읽기</span>
          </button>
          <button
            onClick={() => openWords(bookId)}
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink-faint)',
              border: 'none', background: 'none', cursor: 'pointer',
              transition: 'color var(--dur-fast), border-color var(--dur-fast)',
            }}
          >
            <BarChart3 size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>단어 분포</span>
          </button>
        </div>
      </div>
    )
  }

  // 본문 리더 단계 내비게이션 바 — 뒤로 + 하위 메뉴 탭(책 정보 · 본문 읽기(활성) · 단어 분포, 단어 분포 내비와 대칭).
  function renderReaderNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        <button
          onClick={readerBack}
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
          <span style={{ fontSize: 13 }}>뒤로</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <button
            onClick={() => openBook(readerBookId)}
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink-faint)',
              border: 'none', background: 'none', cursor: 'pointer',
              transition: 'color var(--dur-fast), border-color var(--dur-fast)',
            }}
          >
            <BookOpen size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>책 정보</span>
          </button>
          <button
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink)',
              borderBottom: '2px solid var(--gold)',
              border: 'none', background: 'none', cursor: 'default',
            }}
          >
            <ScrollText size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>본문 읽기</span>
          </button>
          <button
            onClick={() => openWords(readerBookId)}
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink-faint)',
              border: 'none', background: 'none', cursor: 'pointer',
              transition: 'color var(--dur-fast), border-color var(--dur-fast)',
            }}
          >
            <BarChart3 size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>단어 분포</span>
          </button>
        </div>
      </div>
    )
  }

  // 가계도 단계 내비게이션 바 — 뒤로(진입 지점으로 복귀)
  function renderFamilyNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        <button
          onClick={familyBack}
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
          <span style={{ fontSize: 13 }}>뒤로</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 14px', gap: 8 }}>
          {/* 인장 — 가계도 focus 인물(재중심화 시 key 리마운트로 1회 draw, 비큐레이션은 범용 폴백) */}
          <span key={familyId} style={{ color: 'var(--gold)', display: 'inline-flex' }}>
            <PersonSymbol slug={getPersonSlug(familyId)} size={22} draw />
          </span>
          <span style={{ color: 'var(--ink-dim)', fontSize: 13, fontFamily: 'var(--serif)', fontWeight: 600 }}>가계도</span>
        </div>
      </div>
    )
  }

  // 단어 분포 단계 내비게이션 바 — 뒤로 + 하위 메뉴 탭(책 정보 · 단어 분포(활성), 책 상세 내비와 대칭).
  // 책 정보 탭은 대상이 실제 책일 때만(성경 전체 'all'엔 책 상세가 없음).
  function renderWordsNav() {
    return (
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
        zIndex: 20, boxShadow: 'var(--shadow-1)',
        gap: 0,
      }}>
        <button
          onClick={wordsBack}
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
          <span style={{ fontSize: 13 }}>뒤로</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          {wordsBookId && wordsBookId !== 'all' && (
            <button
              onClick={() => openBook(wordsBookId)}
              style={{
                padding: '0 14px', height: '100%',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
                color: 'var(--ink-faint)',
                border: 'none', background: 'none', cursor: 'pointer',
                transition: 'color var(--dur-fast), border-color var(--dur-fast)',
              }}
            >
              <BookOpen size={18} />
              <span style={{ fontSize: 10, lineHeight: 1 }}>책 정보</span>
            </button>
          )}
          <button
            style={{
              padding: '0 14px', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
              color: 'var(--ink)',
              borderBottom: '2px solid var(--gold)',
              border: 'none', background: 'none', cursor: 'default',
            }}
          >
            <BarChart3 size={18} />
            <span style={{ fontSize: 10, lineHeight: 1 }}>단어 분포</span>
          </button>
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
        background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
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
          <span style={{ color: TYPE_COLOR.Book, fontSize: 13, fontFamily: 'var(--serif)', fontWeight: 600 }}>테마 투어</span>
        </div>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100dvh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

      {/* 책등 전역 헤더 — 전 스테이지 상시 표시, 리본 3부 + 테마 토글(ADR-0026) */}
      <SpineHeader
        activeSection={activeSection}
        onSelectSection={handleSelectSection}
        isMobile={isMobile}
      />

      {/* 허브 단계 — 인물 선택 전 */}
      {activeStage === 'hub' && (
        <div className="stage-in" style={{ flex: 1, overflow: 'hidden' }}>
          <PersonHub onSelectPerson={(id) => selectPerson(id, 'intro')} />
        </div>
      )}

      {/* 개요 단계 — 허브에서 진입 */}
      {activeStage === 'overview' && (
        <>
          {renderOverviewNav()}
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <BibleOverviewView
              onSelectNode={openBook}
              selectedNode={bookId}
            />
          </div>
        </>
      )}

      {/* 책 상세 단계 — 개요에서 책 카드 클릭 시 진입. 시트/우측 패널이 아닌 전용 전체화면 페이지(인물 소개 뷰와 같은 패턴). */}
      {activeStage === 'book' && (
        <>
          {renderBookNav()}
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
          {renderFamilyNav()}
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
          {renderWordsNav()}
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

      {/* 본문 리더 단계 — 책 상세 "본문 읽기"에서 진입. 전용 전체화면 페이지(words와 동형, readerBookId·readerChapter 구동). */}
      {activeStage === 'reader' && (
        <>
          {renderReaderNav()}
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
          {renderToursNav()}
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <TourList onSelectTour={selectTour} />
          </div>
        </>
      )}

      {/* 탐험 단계 — 인물/투어 선택 후 지도·타임라인 */}
      {activeStage === 'explore' && (
        <>
          {renderExploreNav()}

          {/* 전체화면 뷰 — 항상 마운트, CSS 토글로 상태 보존 */}
          <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <div style={{ display: exploreView === 'map' ? 'flex' : 'none', height: '100%' }}>
              {/* 무좌표 여정(셋·아벨·에녹 등) — 지도가 무관한 기본 지역만 보여줘 숨기고 전면 리스트로(task#201).
                  MapView는 언마운트하지 않고 display:none(항상 마운트 규약 유지). */}
              {journeyMapless && (
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <JourneyList
                    stops={journeyStops}
                    activeStopIdx={activeStopIdx}
                    onStopSelect={setActiveStopIdx}
                    verseLang={verseLang}
                    setVerseLang={setVerseLang}
                    personName={exploreTourId ? null : explorePersonName}
                    tourName={exploreTourId ? exploreTourName : null}
                    personSlug={exploreTourId ? null : explorePersonSlug}
                    mapless
                  />
                </div>
              )}
              {/* 여정 사이드 리스트 — 데스크톱: 좌측 200px 고정 / 모바일: 숨김(지도 위에 하단 미니시트) */}
              {!isMobile && !journeyMapless && journeyStops && journeyStops.length > 0 && (
                <div style={{ width: 290, flexShrink: 0, overflow: 'hidden' }}>
                  <JourneyList
                    stops={journeyStops}
                    activeStopIdx={activeStopIdx}
                    onStopSelect={setActiveStopIdx}
                    verseLang={verseLang}
                    setVerseLang={setVerseLang}
                    personName={exploreTourId ? null : explorePersonName}
                    tourName={exploreTourId ? exploreTourName : null}
                    personSlug={exploreTourId ? null : explorePersonSlug}
                  />
                </div>
              )}
              <div style={{ flex: 1, overflow: 'hidden', position: 'relative', display: journeyMapless ? 'none' : undefined }}>
                <MapView
                  onSelectNode={selectNode}
                  selectedNode={selectedNode}
                  personId={explorePersonId}
                  isVisible={exploreView === 'map' && !journeyMapless}
                  journeyStops={journeyStops}
                  activeStopIdx={activeStopIdx}
                  onStopSelect={setActiveStopIdx}
                />
                {/* 모바일 여정 — 하단 세로 리스트(데스크톱과 동일 JourneyList 재사용). 📖는 양피지 모달로 연다. */}
                {isMobile && !journeyMapless && journeyStops && journeyStops.length > 0 && (
                  <div style={{
                    position: 'absolute', bottom: 0, left: 0, right: 0,
                    height: `${JOURNEY_SHEET_VH}dvh`, zIndex: 5,
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
                      personSlug={exploreTourId ? null : explorePersonSlug}
                    />
                  </div>
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
                  onSwitchView={setExploreView}
                  onOpenFamily={() => openFamily(explorePersonId)}
                />
              </div>
            )}
            {/* 인물 소개 뷰 — 지도·타임라인·관계와 같은 레벨의 페이지(PersonIntro 전용 컴포넌트, 인물 모드 전용).
                탐험 자기 시트 억제 규칙(sheetOpen ≠ explorePersonId)은 무접촉 — 전용 뷰라 시트가 아니다. */}
            {exploreView === 'intro' && explorePersonId && (
              <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
                <div style={{ maxWidth: 560, margin: '0 auto', padding: '4px 0 48px' }}>
                  <PersonIntro
                    key={explorePersonId}
                    personId={explorePersonId}
                    verseLang={verseLang}
                    setVerseLang={setVerseLang}
                    onSwitchView={setExploreView}
                    onOpenFamily={openFamily}
                    journeyStops={journeyStops}
                    personEventIds={personEventIds}
                  />
                </div>
              </div>
            )}
            {/* 하나님 의존 뷰 — 인물 모드 전용(의존도 도넛 + mode 분해 + 생애 궤적 + 은혜 하이라이트 + 랭킹) */}
            {exploreView === 'reliance' && explorePersonId && (
              <div style={{ height: '100%' }}>
                <RelianceView
                  key={explorePersonId}
                  personId={explorePersonId}
                  personName={explorePersonName}
                  verseLang={verseLang}
                  setVerseLang={setVerseLang}
                  onSelectPerson={selectPerson}
                />
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
                  top: HEADER_H + NAV_H, right: 0, bottom: 0, width: 360,
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
