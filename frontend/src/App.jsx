import { useState } from 'react'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'
import GraphView from './GraphView'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TABS = [
  { key: 'map', label: '지도' },
  { key: 'timeline', label: '타임라인' },
  { key: 'graph', label: '그래프' },
]

function App() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeView, setActiveView] = useState('map')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)

  function handleTabClick(key) {
    setActiveView(key)
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`)
    const data = await res.json()
    setSearchResults(data)
    setShowDropdown(true)
  }

  function handleSelectResult(result) {
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
        background: 'white', borderBottom: '1px solid #ddd',
        zIndex: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => handleTabClick(tab.key)}
            style={{
              padding: '8px 16px', height: '100%',
              fontWeight: activeView === tab.key ? 'bold' : 'normal',
              borderBottom: activeView === tab.key ? '2px solid #333' : '2px solid transparent',
              border: 'none', background: 'none', cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', padding: '4px 8px', position: 'relative' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="검색..."
            style={{ padding: '4px 8px', marginRight: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
          <button onClick={handleSearch} style={{ padding: '4px 8px', cursor: 'pointer' }}>검색</button>
          {showDropdown && (
            <div style={{
              position: 'absolute', top: '100%', right: 0,
              background: 'white', border: '1px solid #ccc', borderRadius: '4px',
              minWidth: '220px', maxHeight: '300px', overflowY: 'auto',
              zIndex: 100, boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            }}>
              {searchResults.length === 0 ? (
                <div style={{ padding: '8px 12px', color: '#666' }}>결과 없음</div>
              ) : (
                searchResults.map(r => (
                  <div
                    key={r.id}
                    onClick={() => handleSelectResult(r)}
                    style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #eee' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
                    onMouseLeave={e => e.currentTarget.style.background = 'white'}
                  >
                    {r.nameKo} <span style={{ color: '#888', fontSize: '0.85em' }}>({r.label})</span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* 전체화면 뷰 */}
      <div style={{ position: 'absolute', inset: 0 }}>
        {activeView === 'map' && <MapView onSelectNode={setSelectedNode} selectedNode={selectedNode} />}
        {activeView === 'timeline' && <TimelineView onSelectNode={setSelectedNode} selectedNode={selectedNode} />}
        {activeView === 'graph' && (
          <div style={{ position: 'absolute', top: NAV_H, left: 0, right: 0, bottom: 0 }}>
            <GraphView onSelectNode={setSelectedNode} selectedNode={selectedNode} />
          </div>
        )}
      </div>

      {/* 오버레이 패널 — 그래프 뷰 제외, 우측에서 슬라이드인 */}
      {activeView !== 'graph' && (
        <div style={{
          position: 'absolute', top: NAV_H, right: 0, bottom: 0, width: 360,
          background: 'white', overflowY: 'auto',
          boxShadow: '-3px 0 12px rgba(0,0,0,0.15)',
          zIndex: 10,
          transform: selectedNode ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.25s ease',
        }}>
          <button
            onClick={() => setSelectedNode(null)}
            style={{
              position: 'absolute', top: 8, right: 8,
              width: 28, height: 28, borderRadius: '50%',
              border: '1px solid #ddd', background: 'white',
              cursor: 'pointer', fontSize: 16, lineHeight: 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >×</button>
          <SidePanel nodeId={selectedNode} onSelectNode={setSelectedNode} />
        </div>
      )}

    </div>
  )
}

export default App
