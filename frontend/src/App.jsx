import { useState, useEffect } from 'react'
import { Map, Clock, Search, X, BookOpen } from 'lucide-react'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import BibleOverviewView from './BibleOverviewView'
import { TYPE_ORDER, typeColor, typeKo, SELECT_HL } from './theme'
import { useNodeSelection } from './useNodeSelection'
import { useSearch } from './useSearch'

const TABS = [
  { key: 'map', icon: Map, label: '지도' },
  { key: 'timeline', icon: Clock, label: '타임라인' },
  { key: 'overview', icon: BookOpen, label: '성경 개요' },
]

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = '(max-width: 768px)'
// 하단 시트 높이(뷰포트 대비 vh). MapView.jsx의 fitBounds 하단 패딩 비율(0.55)과 반드시 일치시킨다.
const SHEET_VH = 55

// 노드 타입 → 색 팔레트(SidePanel과 동일) / 한글 라벨 / 칩 표시 순서

function App() {
  const [activeView, setActiveView] = useState('map')
  // 절 본문 표시 언어('ko'|'en', 기본 ko) — 타임라인·SidePanel 공유. 한 곳에서 바꾸면 다른 곳도 전환.
  const [verseLang, setVerseLang] = useState('ko')
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)

  const {
    selectedNode, selectedNodeMeta, history, personEventIds,
    handleNodeLoaded, selectNode, selectNodeFresh, goBack, closePanel,
  } = useNodeSelection()

  const {
    searchQuery, searchResults, searchError, searchLoading,
    showDropdown, setShowDropdown,
    highlightIndex, setHighlightIndex,
    typeFilter, setTypeFilter,
    typeCounts, filteredResults,
    searchBoxRef, resultRefs,
    onSearchInput, clearSearch,
  } = useSearch()

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  function handleTabClick(key) {
    setActiveView(key)
  }

  // 브리지 — 검색 선택 시 검색 상태 초기화 + 새 탐색 컨텍스트로 노드 선택, 타입별 탭 이동
  function handleSelectResult(result) {
    clearSearch()
    const tabMap = { Person: 'map', Place: 'map', Event: 'timeline', Book: 'overview' }
    const target = tabMap[result.label] ?? 'map'
    setActiveView(target)
    selectNodeFresh(result.id)
  }

  function handleSearchKeyDown(e) {
    if (e.key === 'Escape') { setShowDropdown(false); return }
    if (!showDropdown || filteredResults.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightIndex(i => (i + 1) % filteredResults.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightIndex(i => (i - 1 + filteredResults.length) % filteredResults.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const pick = highlightIndex >= 0 ? filteredResults[highlightIndex] : filteredResults[0]
      if (pick) handleSelectResult(pick)
    }
  }

  const NAV_H = 48

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

      {/* 내비게이션 바 */}
      <div style={{
        height: NAV_H, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        background: '#1a1a2e', borderBottom: 'none',
        zIndex: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
      }}>
        {TABS.map(tab => {
          const Icon = tab.icon
          const active = activeView === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => handleTabClick(tab.key)}
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
        <div ref={searchBoxRef} style={{ flex: 1, display: 'flex', alignItems: 'center', padding: '0 8px', position: 'relative' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={onSearchInput}
              onKeyDown={handleSearchKeyDown}
              onFocus={() => { if (searchResults.length > 0) setShowDropdown(true) }}
              placeholder="검색..."
              style={{
                width: '100%', padding: '6px 36px 6px 12px', boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.1)', color: 'white',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8,
                outline: 'none', fontSize: 14,
              }}
            />
            {searchQuery ? (
              <button
                onClick={clearSearch}
                aria-label="지우기"
                style={{
                  position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', padding: 0,
                }}
              >
                <X size={16} />
              </button>
            ) : (
              <span style={{
                position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                color: 'rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', pointerEvents: 'none',
              }}>
                <Search size={16} />
              </span>
            )}
          </div>
          {showDropdown && (
            <div style={{
              position: 'absolute', top: 'calc(100% + 6px)', right: 0,
              background: '#1e2040', border: '1px solid rgba(124,156,252,0.25)',
              borderRadius: 10, minWidth: '260px', maxHeight: '360px', overflowY: 'auto',
              zIndex: 100, boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            }}>
              {searchError ? (
                <div style={{ padding: '12px 16px', color: '#ff9b9b', fontSize: 13 }}>검색에 실패했습니다</div>
              ) : searchLoading && searchResults.length === 0 ? (
                <div style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>검색 중…</div>
              ) : searchResults.length === 0 ? (
                <div style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>결과 없음</div>
              ) : (
                <>
                  {/* 타입 필터 칩 — 현재 결과에 존재하는 타입만, 각 개수 표시 */}
                  <div style={{
                    display: 'flex', gap: 6, flexWrap: 'wrap', padding: '8px 10px',
                    borderBottom: '1px solid rgba(255,255,255,0.08)',
                    position: 'sticky', top: 0, background: '#1e2040', zIndex: 1,
                  }}>
                    {[{ key: null, ko: '전체', color: '#9aa5b8', count: searchResults.length },
                      ...TYPE_ORDER.filter(t => typeCounts[t]).map(t => ({ key: t, ko: typeKo(t), color: typeColor(t), count: typeCounts[t] })),
                    ].map(chip => {
                      const active = typeFilter === chip.key
                      return (
                        <button
                          key={chip.key ?? 'all'}
                          onClick={() => { setTypeFilter(chip.key); setHighlightIndex(-1) }}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 5,
                            fontSize: 11, padding: '3px 9px', borderRadius: 999, cursor: 'pointer',
                            border: `1px solid ${active ? chip.color : 'rgba(255,255,255,0.15)'}`,
                            background: active ? chip.color : 'transparent',
                            color: active ? '#11131f' : 'rgba(255,255,255,0.7)',
                            fontWeight: active ? 700 : 500,
                          }}
                        >
                          {chip.ko}<span style={{ opacity: 0.75 }}>{chip.count}</span>
                        </button>
                      )
                    })}
                  </div>
                  {/* 결과 목록 — 좌측 타입색 액센트, 하이라이트(키보드/마우스 공유) */}
                  {filteredResults.map((r, i) => (
                    <div
                      key={r.id}
                      ref={el => { resultRefs.current[i] = el }}
                      onClick={() => handleSelectResult(r)}
                      onMouseEnter={() => setHighlightIndex(i)}
                      style={{
                        padding: '10px 14px', cursor: 'pointer',
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                        borderLeft: `3px solid ${typeColor(r.label)}`,
                        display: 'flex', alignItems: 'center', gap: 10, color: 'white',
                        background: i === highlightIndex ? SELECT_HL : 'transparent',
                      }}
                    >
                      <span style={{ fontSize: 14, fontWeight: 500, flex: 1 }}>{r.nameKo}</span>
                      <span style={{
                        fontSize: 10, color: typeColor(r.label), background: 'rgba(255,255,255,0.08)',
                        borderRadius: 4, padding: '2px 6px', flexShrink: 0,
                      }}>{typeKo(r.label)}</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 전체화면 뷰 — 항상 마운트, CSS 토글로 상태 보존 */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <div style={{ display: activeView === 'map' ? 'block' : 'none', flex: 1, overflow: 'hidden', height: '100%' }}>
          <MapView
            onSelectNode={selectNode}
            selectedNode={selectedNode}
            isVisible={activeView === 'map'}
          />
        </div>
        <div style={{ display: activeView === 'timeline' ? 'block' : 'none', flex: 1, overflow: 'hidden', height: '100%' }}>
          <TimelineView
            onSelectNode={selectNode}
            selectedNode={selectedNode}
            bookFilter={selectedNodeMeta?.label === 'Book' ? selectedNodeMeta : null}
            personFilter={selectedNodeMeta?.label === 'Person' ? personEventIds : null}
            personName={selectedNodeMeta?.label === 'Person' ? selectedNodeMeta.nameKo : null}
            verseLang={verseLang}
            setVerseLang={setVerseLang}
          />
        </div>
        <div style={{ display: activeView === 'overview' ? 'block' : 'none', flex: 1, overflow: 'hidden', height: '100%' }}>
          <BibleOverviewView
            onSelectNode={selectNode}
            selectedNode={selectedNode}
          />
        </div>
      </div>

      {/* 오버레이 패널 — 데스크톱: 우측 슬라이드인 / 모바일: 하단 시트(지도·마커가 위에 보이도록) */}
      <div style={{
          position: 'absolute', background: 'white', overflowY: 'auto', zIndex: 10,
          transition: 'transform 0.25s ease',
          ...(isMobile
            ? {
                left: 0, right: 0, bottom: 0, height: `${SHEET_VH}vh`,
                boxShadow: '0 -3px 12px rgba(0,0,0,0.15)',
                transform: selectedNode ? 'translateY(0)' : 'translateY(100%)',
              }
            : {
                top: NAV_H, right: 0, bottom: 0, width: 360,
                boxShadow: '-3px 0 12px rgba(0,0,0,0.15)',
                transform: selectedNode ? 'translateX(0)' : 'translateX(100%)',
              }),
        }}>
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
          <SidePanel nodeId={selectedNode} onSelectNode={selectNode} onBack={goBack} canGoBack={history.length > 0} onNodeLoaded={handleNodeLoaded} verseLang={verseLang} setVerseLang={setVerseLang} />
        </div>

    </div>
  )
}

export default App
