import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const DEFAULT_NODE = 'recjNRR60PAuFtjha' // 모세

const TYPE_COLOR = {
  Person: '#4a90d9',
  Place: '#27ae60',
  Event: '#e67e22',
  PeopleGroup: '#8e44ad',
}

function buildPositions(centerId, neighbors, W, H) {
  const PAD = 60
  const cx = W / 2
  const cy = H / 2
  const R = Math.min(W - PAD * 2, H - PAD * 2) / 2
  const positions = { [centerId]: { x: cx, y: cy } }
  neighbors.forEach((n, i) => {
    const angle = (i / neighbors.length) * 2 * Math.PI - Math.PI / 2
    positions[n.id] = { x: cx + R * Math.cos(angle), y: cy + R * Math.sin(angle) }
  })
  return positions
}

export default function GraphView({ onSelectNode, selectedNode }) {
  const containerRef = useRef(null)
  const [overlay, setOverlay] = useState(null)

  useEffect(() => {
    const id = selectedNode || DEFAULT_NODE
    let cy = null

    fetch(`${API_URL}/node/${id}`)
      .then(r => r.json())
      .then(data => {
        const center = { id: data.id, label: data.nameKo || data.name, nodeType: data.label }
        const neighbors = data.neighbors || []

        if (selectedNode) {
          setOverlay({
            name: data.name,
            nameKo: data.nameKo || data.name,
            label: data.label,
            neighborCount: neighbors.length,
          })
        }

        const W = containerRef.current.clientWidth || window.innerWidth
        const H = containerRef.current.clientHeight || window.innerHeight
        const positions = buildPositions(center.id, neighbors, W, H)

        const nodes = [
          { data: { id: center.id, label: center.label, nodeType: center.nodeType, isCenter: 1 } },
          ...neighbors.map(n => ({
            data: { id: n.id, label: n.nameKo || n.name, nodeType: n.label, isCenter: 0 },
          })),
        ]
        const edges = neighbors.map((n, i) => ({
          data: { id: `e${i}`, source: center.id, target: n.id, relation: n.relation },
        }))

        cy = cytoscape({
          container: containerRef.current,
          elements: [...nodes, ...edges],
          style: [
            {
              selector: 'node',
              style: {
                'background-color': '#999',
                'label': 'data(label)',
                'font-size': '9px',
                'text-valign': 'bottom',
                'text-margin-y': 2,
                'color': '#333',
                'width': 14,
                'height': 14,
              },
            },
            { selector: 'node[nodeType = "Person"]', style: { 'background-color': TYPE_COLOR.Person } },
            { selector: 'node[nodeType = "Place"]', style: { 'background-color': TYPE_COLOR.Place } },
            { selector: 'node[nodeType = "Event"]', style: { 'background-color': TYPE_COLOR.Event } },
            { selector: 'node[nodeType = "PeopleGroup"]', style: { 'background-color': TYPE_COLOR.PeopleGroup } },
            {
              selector: 'node[isCenter = 1]',
              style: { 'width': 26, 'height': 26, 'border-width': 3, 'border-color': '#333', 'font-size': '11px', 'font-weight': 'bold' },
            },
            { selector: 'edge', style: { 'width': 1, 'line-color': '#ddd', 'curve-style': 'bezier' } },
          ],
          layout: {
            name: 'preset',
            positions: node => positions[node.id()],
            fit: false,
            animate: false,
          },
          zoom: 1,
          pan: { x: 0, y: 0 },
          userZoomingEnabled: true,
          userPanningEnabled: true,
        })

        cy.on('tap', 'node', evt => onSelectNode(evt.target.id()))
        cy.fit(cy.elements(), 40)
      })
      .catch(() => {})

    return () => { if (cy) cy.destroy() }
  }, [selectedNode, onSelectNode])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />


      {/* 하단 오버레이 */}
      {overlay && (
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          background: 'white', borderTop: '1px solid #e0e0e0',
          padding: '12px 16px 20px',
          boxShadow: '0 -2px 12px rgba(0,0,0,0.12)',
          zIndex: 20,
        }}>
          <button
            onClick={() => { setOverlay(null); onSelectNode(null) }}
            style={{
              position: 'absolute', top: 10, right: 12,
              width: 26, height: 26, borderRadius: '50%',
              border: '1px solid #ddd', background: 'white',
              cursor: 'pointer', fontSize: 15,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >×</button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{
              background: TYPE_COLOR[overlay.label] || '#999',
              color: 'white', borderRadius: 4,
              padding: '2px 8px', fontSize: 11,
            }}>{overlay.label}</span>
            <strong style={{ fontSize: 16 }}>{overlay.nameKo}</strong>
            {overlay.nameKo !== overlay.name && (
              <span style={{ fontSize: 12, color: '#888' }}>{overlay.name}</span>
            )}
          </div>
          <div style={{ fontSize: 12, color: '#666' }}>직접 연결: {overlay.neighborCount}개 노드</div>
        </div>
      )}
    </div>
  )
}
