import { useState } from 'react'
import MapView from './MapView'
import SidePanel from './SidePanel'
import TimelineView from './TimelineView'

const TABS = [
  { key: 'map', label: '지도' },
  { key: 'timeline', label: '타임라인' },
  { key: 'graph', label: '그래프' },
]

function App() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeView, setActiveView] = useState('map')

  function handleTabClick(key) {
    setActiveView(key)
    setSelectedNode(null)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      <div style={{ flex: 'none', display: 'flex', borderBottom: '1px solid #ccc' }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => handleTabClick(tab.key)}
            style={{
              padding: '8px 16px',
              fontWeight: activeView === tab.key ? 'bold' : 'normal',
              borderBottom: activeView === tab.key ? '2px solid #333' : '2px solid transparent',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div style={{ flex: 1, display: 'flex' }}>
        <div style={{ flex: '0 0 70%', height: '100%' }}>
          {activeView === 'map' && <MapView onSelectNode={setSelectedNode} />}
          {activeView === 'timeline' && <TimelineView onSelectNode={setSelectedNode} />}
          {activeView === 'graph' && <div style={{ padding: '2rem' }}>그래프 뷰 준비 중</div>}
        </div>
        <div style={{ flex: '0 0 30%', height: '100%', overflowY: 'auto', borderLeft: '1px solid #ccc' }}>
          <SidePanel nodeId={selectedNode} />
        </div>
      </div>
    </div>
  )
}

export default App
