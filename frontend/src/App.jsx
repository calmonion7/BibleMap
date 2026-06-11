import { useState, useEffect, useCallback, useRef } from 'react'
import { Map, Clock, Network, Search } from 'lucide-react'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import GraphView from './GraphView'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TABS = [
  { key: 'map', icon: Map },
  { key: 'timeline', icon: Clock },
  { key: 'graph', icon: Network },
]

// 모바일(좁은 뷰포트) 분기 — 이 폭 이하에서 상세 패널을 우측 사이드패널 대신 하단 시트로 띄운다.
const MOBILE_QUERY = '(max-width: 768px)'
// 하단 시트 높이(뷰포트 대비 vh). MapView.jsx의 fitBounds 하단 패딩 비율(0.55)과 반드시 일치시킨다.
const SHEET_VH = 55

function App() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeView, setActiveView] = useState('map')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchError, setSearchError] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)
  const [history, setHistory] = useState([])
  const selectedNodeRef = useRef(null)
  useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  function handleTabClick(key) {
    setActiveView(key)
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return
    setSearchError(false)
    try {
      const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`)
      if (!res.ok) throw new Error(res.status)
      const data = await res.json()
      setSearchResults(data)
    } catch {
      setSearchResults([])
      setSearchError(true)
    }
    setShowDropdown(true)
  }

  // 노드 선택 — 직전 노드를 히스토리에 쌓아 패널 뒤로가기를 지원
  // useCallback([])으로 참조를 안정화: selectedNode 변경 시 MapView 등의 useEffect가 재실행되어
  // expandPlace fetch가 abort되는 버그 방지 (selectedNodeRef로 최신값 읽음)
  const selectNode = useCallback((id) => {
    if (id === selectedNodeRef.current) return
    if (selectedNodeRef.current) setHistory(h => [...h, selectedNodeRef.current])
    setSelectedNode(id)
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
  }

  const NAV_H = 48

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden' }}>

      {/* 내비게이션 바 — 지도 위에 플로팅 */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: NAV_H,
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
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', padding: '0 8px', position: 'relative' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="검색..."
              style={{
                width: '100%', padding: '6px 36px 6px 12px', boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.1)', color: 'white',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8,
                outline: 'none', fontSize: 14,
              }}
            />
            <button
              onClick={handleSearch}
              style={{
                position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', padding: 0,
              }}
            >
              <Search size={16} />
            </button>
          </div>
          {showDropdown && (
            <div style={{
              position: 'absolute', top: 'calc(100% + 6px)', right: 0,
              background: '#1e2040', border: '1px solid rgba(124,156,252,0.25)',
              borderRadius: 10, minWidth: '240px', maxHeight: '320px', overflowY: 'auto',
              zIndex: 100, boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            }}>
              {searchError ? (
                <div style={{ padding: '12px 16px', color: '#ff9b9b', fontSize: 13 }}>검색에 실패했습니다</div>
              ) : searchResults.length === 0 ? (
                <div style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>결과 없음</div>
              ) : (
                searchResults.map(r => (
                  <div
                    key={r.id}
                    onClick={() => handleSelectResult(r)}
                    style={{
                      padding: '10px 16px', cursor: 'pointer',
                      borderBottom: '1px solid rgba(255,255,255,0.06)',
                      display: 'flex', alignItems: 'center', gap: 10,
                      color: 'white',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(124,156,252,0.12)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <span style={{ fontSize: 14, fontWeight: 500 }}>{r.nameKo}</span>
                    <span style={{
                      fontSize: 10, color: '#7c9cfc', background: 'rgba(124,156,252,0.15)',
                      borderRadius: 4, padding: '2px 6px', flexShrink: 0,
                    }}>{r.label}</span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* 전체화면 뷰 */}
      <div style={{ position: 'absolute', inset: 0 }}>
        {activeView === 'map' && <MapView onSelectNode={selectNode} selectedNode={selectedNode} />}
        {activeView === 'timeline' && <TimelineView onSelectNode={selectNode} selectedNode={selectedNode} />}
        {activeView === 'graph' && (
          <div style={{ position: 'absolute', top: NAV_H, left: 0, right: 0, bottom: 0 }}>
            <GraphView onSelectNode={selectNode} selectedNode={selectedNode} />
          </div>
        )}
      </div>

      {/* 오버레이 패널 — 그래프 뷰 제외. 데스크톱: 우측 슬라이드인 / 모바일: 하단 시트(지도·마커가 위에 보이도록) */}
      {activeView !== 'graph' && (
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
          <SidePanel nodeId={selectedNode} onSelectNode={selectNode} onBack={goBack} canGoBack={history.length > 0} />
        </div>
      )}

    </div>
  )
}

export default App
