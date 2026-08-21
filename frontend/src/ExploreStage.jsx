import { useMemo, useEffect } from 'react'
import { Route, Clock, UserRound, ScrollText, Users, HeartHandshake, Network, Play } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import StageNav from './StageNav'
import BookmarkToggle from './BookmarkToggle'
import PersonSymbol from './personSymbols'
import MapView from './MapView'
import TimelineView from './TimelineView'
import RelationsView from './RelationsView'
import RelianceView from './RelianceView'
import PersonIntro from './PersonIntro'
import TourIntro from './TourIntro'
import TourPlaybackCard from './TourPlayback'
import JourneyList from './JourneyList'
import { journeyStopGroups } from './mapGeo'
import { JOURNEY_SHEET_VH } from './constants'

// 탐험 토글 정의 — 지도 라벨은 "여정"(인물이 지도 위에 남긴 이동 경로)
const EXPLORE_TABS = [
  { key: 'map', icon: Route, label: '여정' },
  { key: 'timeline', icon: Clock, label: '연표' },  // '타임라인'은 모바일 6탭 폭에서 2줄 — 2글자로 축약
]
const INTRO_TAB = { key: 'intro', icon: UserRound, label: '소개' }
// 투어 개요 탭 — 인물 소개 탭의 투어판(task#222). 같은 'intro' 키로 뷰 상태 공유, 라벨·아이콘만 투어용.
const TOUR_INTRO_TAB = { key: 'intro', icon: ScrollText, label: '개요' }
const RELATIONS_TAB = { key: 'relations', icon: Users, label: '관계' }
// 하나님 의존 — 관계와 동형 탭(setExploreView). 그 인물의 하나님 의존도·궤적.
// 라벨은 짧게 '의존'(모바일 6탭 폭에서 '하나님 의존'은 3줄로 감김) — 아이콘·본문 헤더가 맥락 전달.
const RELIANCE_TAB = { key: 'reliance', icon: HeartHandshake, label: '의존' }
// 가계도 — 탭 전환(setExploreView)이 아니라 전용 스테이지(openFamily) 진입. 관계 옆에 배치.
// 라벨 '족보'(2글자) — '가계도'는 모바일 6탭 폭에서 2줄로 감김.
const FAMILY_TAB = { key: 'family', icon: Network, label: '족보' }

// 탐험 단계 — 인물/투어 선택 후의 지도·연표·관계·소개·투어개요·의존 6뷰 + 여정 리스트 + 투어 재생.
// journey는 App이 소유하는 useExploreJourney의 반환, playback은 App이 소유하는 useTourPlayback의 반환
// (수명 이유는 각 훅 상단 주석 — 족보 진입·헤더 리본 이탈 등으로 이 컴포넌트가 재마운트되므로
// 여정·재생 상태를 여기서 소유하면 안 된다).
export default function ExploreStage({
  journey,
  playback,
  exploreView, setExploreView,
  explorePersonId, explorePersonName, explorePersonSlug, explorePersonEra, exploreTourId,
  backToHub, toursBack, openFamily, selectPerson, curatedIds, getPersonSlug,
  selectedNode, selectedNodeMeta, selectNode,
  verseLang, setVerseLang, isMobile,
  bookmarkEntry, isBookmarked, onToggleBookmark, onRecordRecent, onOpenPlace,
}) {
  const { journeyStops, activeStopIdx, setActiveStopIdx, exploreTourName, exploreTourMeta, personEventIds } = journey

  // 투어 타임라인 필터 — TimelineView가 Set.has()로 쓰므로 Set으로, 참조 안정화(인물의 personEventIds와 동일 형태)
  const tourEventIds = useMemo(
    () => (exploreTourId && journeyStops ? new Set(journeyStops.map(s => s.eventId)) : null),
    [exploreTourId, journeyStops],
  )
  // 무좌표 여정(task#201) — 정차 전부가 지도 좌표 없음(셋·아벨·에녹) → 지도 대신 전면 리스트
  const journeyMapless = !!(journeyStops && journeyStops.length > 0 && !journeyStops.some(s => s.lng != null && s.lat != null))

  // 투어 자동재생(task#223) — 사건 단위 시퀀서(playback은 App 소유 prop, task#263 — 헤더 리본 이탈→뒤로가기
  // 재마운트에도 재생 상태가 살아남게). 카메라는 activeStopIdx를 구독한 effect가 구동.
  // 재생 중 활성 정차지 그룹 인덱스 — playback.idx를 그룹 인덱스로 파생(effect+setState 대신, task#253).
  // 무좌표 사건은 직전 좌표 사건 그룹을 유지(카메라 유지·카드만 교체 규약).
  const playbackStopIdx = useMemo(() => {
    if (playback.idx == null || !journeyStops) return null
    const groups = journeyStopGroups(journeyStops)
    for (let i = playback.idx; i >= 0; i--) {
      const s = journeyStops[i]
      if (s && s.lng != null && s.lat != null) {
        const gi = groups.findIndex(g => g.stops.some(x => x.eventId === s.eventId))
        if (gi >= 0) return gi
      }
    }
    return null
  }, [playback.idx, journeyStops])
  // 재생 중이면 파생 인덱스, 아니면 사용자가 클릭한 activeStopIdx — 지도·리스트 하이라이트/카메라 구동원.
  const effectiveStopIdx = playback.active && playbackStopIdx != null ? playbackStopIdx : activeStopIdx
  // 투어 이탈·탭 전환 시 재생 종료(경로선 전체 복원은 MapView가 playbackIdx null로 처리)
  useEffect(() => {
    if (playback.active && (exploreTourId == null || exploreView !== 'map')) playback.exit()
  }, [exploreTourId, exploreView, playback])

  // 탐험 내비 — 투어/인물 모드에 따라 복귀 대상·제목·색이 갈린다
  const isTour = exploreTourId != null
  const heading = isTour ? exploreTourName : explorePersonName

  // 이어보기 기록(task#268) — 제목이 로드된 뒤 한 번. 뷰 토글로는 새 항목이 쌓이지 않게
  // 항목 해시를 뷰 없는 기본 해시로 둔다(훅이 같은 해시를 최신으로 승격).
  useEffect(() => {
    if (!bookmarkEntry?.hash || !heading) return
    onRecordRecent?.({ ...bookmarkEntry, label: heading })
  }, [bookmarkEntry, heading, onRecordRecent])

  return (
    <>
      {/* 모바일 인물 모드는 보조 라벨을 생략한다 — 인장이 차지한 폭을 회수해 6탭(족보까지)이 뷰포트 안에 들게 */}
      <StageNav
        onBack={isTour ? toursBack : backToHub}
        auxLabel={isMobile && !isTour ? null : isTour ? '테마 목록' : '다른 인물'}
        trailing={bookmarkEntry ? (
          <BookmarkToggle
            saved={isBookmarked}
            onToggle={() => onToggleBookmark({ ...bookmarkEntry, label: heading || bookmarkEntry.label })}
          />
        ) : null}
        lead={(
          <>
            {/* 인장 — 탐험 중 인물의 상징물(인물 전환 시에만 key 리마운트로 1회 draw, 탭 전환엔 정적) */}
            {!isTour && explorePersonId && (
              <span key={explorePersonId} style={{ color: 'var(--gold)', flexShrink: 0, display: 'inline-flex' }}>
                <PersonSymbol slug={getPersonSlug(explorePersonId)} size={isMobile ? 20 : 26} draw />
              </span>
            )}
            {heading ? (
              <span style={{ fontSize: 13, fontFamily: 'var(--serif)', color: isTour ? TYPE_COLOR.Book : 'var(--gold)', fontWeight: 600, maxWidth: isMobile ? 80 : 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {heading}
              </span>
            ) : null}
          </>
        )}
      >
        {(explorePersonId && !exploreTourId ? [INTRO_TAB, ...EXPLORE_TABS, RELATIONS_TAB, RELIANCE_TAB, FAMILY_TAB] : [TOUR_INTRO_TAB, ...EXPLORE_TABS]).map(tab => (
          <StageNav.Tab
            key={tab.key}
            icon={tab.icon}
            label={tab.label}
            active={exploreView === tab.key}
            onClick={() => tab.key === 'family' ? openFamily(explorePersonId) : setExploreView(tab.key)}
          />
        ))}
      </StageNav>

      {/* 전체화면 뷰 — 항상 마운트, CSS 토글로 상태 보존 */}
      <div className="stage-in" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <div style={{ display: exploreView === 'map' ? 'flex' : 'none', height: '100%' }}>
          {/* 무좌표 여정(셋·아벨·에녹 등) — 지도가 무관한 기본 지역만 보여줘 숨기고 전면 리스트로(task#201).
              MapView는 언마운트하지 않고 display:none(항상 마운트 규약 유지). */}
          {journeyMapless && (
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <JourneyList
                onOpenPlace={onOpenPlace}
                stops={journeyStops}
                activeStopIdx={effectiveStopIdx}
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
                onOpenPlace={onOpenPlace}
                stops={journeyStops}
                activeStopIdx={effectiveStopIdx}
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
              onOpenPlace={onOpenPlace}
              onSelectNode={selectNode}
              selectedNode={selectedNode}
              personId={explorePersonId}
              pmEnabled={(explorePersonId ? explorePersonEra : exploreTourMeta?.era) === '신약'}
              isVisible={exploreView === 'map' && !journeyMapless}
              journeyStops={journeyStops}
              activeStopIdx={effectiveStopIdx}
              onStopSelect={setActiveStopIdx}
              playbackIdx={playback.idx}
            />
            {/* ▶ 투어 재생 — 투어 모드 지도 상단 진입점(task#223). 재생 중엔 카드가 컨트롤 담당. */}
            {exploreTourId != null && !playback.active && journeyStops && journeyStops.length > 0 && (
              <button className="pressable" onClick={playback.start} style={{
                position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)', zIndex: 6,
                display: 'flex', alignItems: 'center', gap: 6, padding: '9px 18px', borderRadius: 999,
                background: TYPE_COLOR.Book, color: '#fff', border: 'none', cursor: 'pointer',
                fontSize: 13, fontWeight: 700, font: 'inherit', boxShadow: 'var(--shadow-2)',
              }}>
                <Play size={14} /> 투어 재생
              </button>
            )}
            {/* 재생 해설 카드 — 데스크톱: 지도 위 오버레이 / 모바일: 하단 시트 영역 대체.
                장면 스케치(task#226)는 카드 상단 삽화로 통합돼 카드가 렌더한다. */}
            {exploreTourId != null && playback.active && (
              <TourPlaybackCard
                stops={journeyStops}
                tourId={exploreTourId}
                idx={playback.idx}
                playing={playback.playing}
                onToggle={playback.toggle}
                onPrev={playback.prev}
                onNext={playback.next}
                onExit={playback.exit}
                isMobile={isMobile}
              />
            )}
            {/* 모바일 여정 — 하단 세로 리스트(데스크톱과 동일 JourneyList 재사용). 📖는 양피지 모달로 연다. 재생 중엔 해설 카드가 대체. */}
            {isMobile && !journeyMapless && !playback.active && journeyStops && journeyStops.length > 0 && (
              <div style={{
                position: 'absolute', bottom: 0, left: 0, right: 0,
                height: `${JOURNEY_SHEET_VH}dvh`, zIndex: 5,
                borderTop: '1px solid var(--line-strong)',
                boxShadow: 'var(--shadow-2)',
              }}>
                <JourneyList
                onOpenPlace={onOpenPlace}
                  stops={journeyStops}
                  activeStopIdx={effectiveStopIdx}
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
        {/* 투어 개요 뷰 — 인물 소개의 투어판(TourIntro, task#222). subtitle·description·era + 정차지 조망. */}
        {exploreView === 'intro' && exploreTourId != null && (
          <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
            <div style={{ maxWidth: 560, margin: '0 auto', padding: '4px 0 48px' }}>
              <TourIntro
                key={exploreTourId}
                title={exploreTourName}
                subtitle={exploreTourMeta?.subtitle}
                era={exploreTourMeta?.era}
                description={exploreTourMeta?.description}
                journeyStops={journeyStops}
                onSwitchView={setExploreView}
                onPlay={() => { setExploreView('map'); playback.start() }}
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
  )
}
