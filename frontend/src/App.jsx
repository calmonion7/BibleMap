import { useState, useEffect, useCallback, useRef } from 'react'
import { Map, Clock, Search, X } from 'lucide-react'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import { TYPE_ORDER, typeColor, typeKo, SELECT_HL } from './theme'
import { apiGet } from './api'

const TABS = [
  { key: 'map', icon: Map },
  { key: 'timeline', icon: Clock },
]

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = '(max-width: 768px)'
// 하단 시트 높이(뷰포트 대비 vh). MapView.jsx의 fitBounds 하단 패딩 비율(0.55)과 반드시 일치시킨다.
const SHEET_VH = 55

// 노드 타입 → 색 팔레트(SidePanel과 동일) / 한글 라벨 / 칩 표시 순서

function App() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedNodeMeta, setSelectedNodeMeta] = useState(null) // {label, nameKo, startYear, endYear}
  const [activeView, setActiveView] = useState('map')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchError, setSearchError] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const [typeFilter, setTypeFilter] = useState(null)
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)
  const [history, setHistory] = useState([])
  // 절 본문 표시 언어('ko'|'en', 기본 ko) — 타임라인·SidePanel 공유. 한 곳에서 바꾸면 다른 곳도 전환.
  const [verseLang, setVerseLang] = useState('ko')
  const [personEventIds, setPersonEventIds] = useState(null)
  const selectedNodeRef = useRef(null)
  const searchBoxRef = useRef(null)
  const resultRefs = useRef([])
  useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])

  // 선택된 노드의 메타 정보(label, Book 연대) 조회 — SidePanel과 별도 fetch 없이 콜백으로 수신
  const handleNodeLoaded = useCallback((node) => {
    if (!node) return
    setSelectedNodeMeta({
      label: node.label,
      nameKo: node.nameKo,
      startYear: node.properties?.startYear ?? null,
      endYear: node.properties?.endYear ?? null,
    })
    if (node.label === 'Person') {
      apiGet(`/person/${node.id}/event-ids`)
        .then(data => setPersonEventIds(new Set(data.eventIds)))
        .catch(() => setPersonEventIds(null))
    } else {
      setPersonEventIds(null)
    }
  }, [])

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // 실시간 검색 — 입력이 바뀌면 250ms 디바운스 후 자동 조회. 직전 요청은 abort로 경쟁 차단.
  // setState는 전부 setTimeout/async 콜백 안에서만(effect 동기 본문 setState 금지 — react-hooks v7).
  useEffect(() => {
    const q = searchQuery.trim()
    if (!q) return
    const ctrl = new AbortController()
    const timer = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const data = await apiGet(`/search?q=${encodeURIComponent(q)}`, { signal: ctrl.signal })
        setSearchResults(data)
        setSearchError(false)
      } catch (e) {
        if (e.name === 'AbortError') return // 더 최신 입력이 진행 중 — 무시
        setSearchResults([]); setSearchError(true)
      }
      setSearchLoading(false)
      setShowDropdown(true)
      setHighlightIndex(-1)
      setTypeFilter(null)
    }, 250)
    return () => { clearTimeout(timer); ctrl.abort() }
  }, [searchQuery])

  // 드롭다운 바깥 클릭 시 닫기
  useEffect(() => {
    if (!showDropdown) return
    const onDown = (e) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target)) setShowDropdown(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [showDropdown])

  // 키보드 하이라이트가 보이도록 스크롤
  useEffect(() => {
    if (highlightIndex >= 0) resultRefs.current[highlightIndex]?.scrollIntoView({ block: 'nearest' })
  }, [highlightIndex])

  function handleTabClick(key) {
    setActiveView(key)
  }

  function onSearchInput(e) {
    const v = e.target.value
    setSearchQuery(v)
    if (!v.trim()) { setSearchResults([]); setSearchError(false); setSearchLoading(false); setShowDropdown(false) }
  }

  // 노드 선택 — 직전 노드를 히스토리에 쌓아 패널 뒤로가기를 지원
  // useCallback([])으로 참조를 안정화: selectedNode 변경 시 MapView 등의 useEffect가 재실행되어
  // expandPlace fetch가 abort되는 버그 방지 (selectedNodeRef로 최신값 읽음)
  const selectNode = useCallback((id) => {
    if (id === selectedNodeRef.current) return
    if (selectedNodeRef.current) setHistory(h => [...h, selectedNodeRef.current])
    setSelectedNode(id)
    setSelectedNodeMeta(null)
    setPersonEventIds(null)
  }, [])

  function goBack() {
    setSelectedNode(history[history.length - 1] ?? null)
    setHistory(h => h.slice(0, -1))
  }

  function closePanel() {
    setHistory([])
    setSelectedNode(null)
  }

  function handleSelectResult(result) {
    setHistory([]) // 새 검색은 새 탐색 컨텍스트 — 히스토리 리셋
    setSelectedNode(result.id)
    setShowDropdown(false)
    setSearchQuery('')
    setSearchResults([])
    setHighlightIndex(-1)
    setTypeFilter(null)
  }

  function clearSearch() {
    setSearchQuery('')
    setSearchResults([])
    setShowDropdown(false)
    setHighlightIndex(-1)
    setTypeFilter(null)
  }

  const typeCounts = searchResults.reduce((m, r) => { m[r.label] = (m[r.label] || 0) + 1; return m }, {})
  const filteredResults = typeFilter ? searchResults.filter(r => r.label === typeFilter) : searchResults

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
                padding: '0 18px', height: '100%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: active ? 'white' : 'rgba(255,255,255,0.5)',
                borderBottom: active ? '2px solid #7c9cfc' : '2px solid transparent',
                border: 'none', background: 'none', cursor: 'pointer',
                transition: 'color 0.15s',
              }}
            >
              <Icon size={20} />
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

      {/* 전체화면 뷰 */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {activeView === 'map' && (
          <MapView
            onSelectNode={selectNode}
            selectedNode={selectedNode}
          />
        )}
        {activeView === 'timeline' && (
          <TimelineView
            onSelectNode={selectNode}
            selectedNode={selectedNode}
            bookFilter={selectedNodeMeta?.label === 'Book' ? selectedNodeMeta : null}
            personFilter={selectedNodeMeta?.label === 'Person' ? personEventIds : null}
            personName={selectedNodeMeta?.label === 'Person' ? selectedNodeMeta.nameKo : null}
            verseLang={verseLang}
            setVerseLang={setVerseLang}
          />
        )}
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
              width: 28, height: 28, borderRadius: '50%',
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
