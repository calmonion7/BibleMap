import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import coseBilkent from 'cytoscape-cose-bilkent'
import expandCollapse from 'cytoscape-expand-collapse'
import { TYPE_COLOR, TYPE_KO, TYPE_ORDER } from './theme'
cytoscape.use(coseBilkent)
cytoscape.use(expandCollapse)

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const DEFAULT_NODE = 'recjNRR60PAuFtjha' // 모세

const TYPE_LABEL_KO = {
  Person: '관련 인물',
  Event: '관련 사건',
  PeopleGroup: '관련 그룹',
  Place: '관련 장소',
}

export default function GraphView({ onSelectNode, selectedNode }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  const [overlay, setOverlay] = useState(null)
  const [showLegend, setShowLegend] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!cyRef.current) return
    cyRef.current.fit(cyRef.current.elements(), overlay ? 100 : 40)
  }, [overlay])

  useEffect(() => {
    const id = selectedNode || DEFAULT_NODE
    let cy = null
    let cancelled = false

    Promise.all([
      fetch(`${API_URL}/node/${id}`).then(r => r.ok ? r.json() : Promise.reject(r.status)),
      fetch(`${API_URL}/node/${id}/neighbors/grouped`).then(r => r.ok ? r.json() : Promise.reject(r.status)),
    ])
      .then(([data, grouped]) => {
        if (!cancelled) setError(false)
        const center = { id: data.id, label: data.nameKo || data.name, nodeType: data.label }
        const totalNeighborCount = Object.values(grouped).reduce((sum, arr) => sum + arr.length, 0)

        if (selectedNode) {
          setOverlay({
            name: data.name,
            nameKo: data.nameKo || data.name,
            label: data.label,
            neighborCount: totalNeighborCount,
          })
        }

        const nodes = [
          { data: { id: center.id, label: center.label, nodeType: center.nodeType, isCenter: 1 } },
        ]
        const edges = []

        Object.entries(TYPE_LABEL_KO).forEach(([type, labelKo]) => {
          const group = grouped[type] || []
          if (group.length === 0) return

          const parentId = `group-${type}`
          nodes.push({
            data: { id: parentId, label: `${labelKo} (${group.length})`, nodeType: 'GroupParent' },
          })

          group.forEach((n, i) => {
            nodes.push({
              data: { id: n.id, label: n.nameKo || n.name, nodeType: type, isCenter: 0, parent: parentId },
            })
            edges.push({
              data: { id: `e-${type}-${i}`, source: center.id, target: n.id, relation: n.relation },
            })
          })
        })

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
            {
              selector: 'node[nodeType = "GroupParent"]',
              style: {
                'background-color': '#f5f5f5',
                'border-width': 2,
                'border-color': '#ccc',
                'label': 'data(label)',
                'font-size': '10px',
                'text-valign': 'top',
                'text-halign': 'center',
                'color': '#555',
                'text-margin-y': -4,
              },
            },
            { selector: 'edge', style: { 'width': 1, 'line-color': '#ddd', 'curve-style': 'bezier' } },
          ],
          layout: {
            name: 'cose-bilkent',
            animate: false,
            randomize: false,
            nodeDimensionsIncludeLabels: true,
          },
          zoom: 1,
          pan: { x: 0, y: 0 },
          userZoomingEnabled: true,
          userPanningEnabled: true,
        })

        const ecApi = cy.expandCollapse({
          layoutBy: { name: 'cose-bilkent', animate: false, randomize: false },
          undoable: false,
          fisheye: false,
          animate: false,
        })
        ecApi.collapseAll()

        cy.on('tap', 'node', evt => {
          if (evt.target.data('nodeType') === 'GroupParent') return
          onSelectNode(evt.target.id())
        })
        cy.on('expandcollapse.afterexpand expandcollapse.aftercollapse', () => {
          cy.fit(cy.elements(), 40)
        })
        cyRef.current = cy
        cy.fit(cy.elements(), 40)
      })
      .catch(() => { if (!cancelled) setError(true) })

    return () => { cancelled = true; if (cy) { cy.destroy(); cyRef.current = null } }
  }, [selectedNode, onSelectNode])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {error && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#999', fontSize: 14, pointerEvents: 'none',
        }}>
          그래프를 불러오지 못했습니다
        </div>
      )}

      <button
        onClick={() => setShowLegend(v => !v)}
        style={{
          position: 'absolute', top: 8, right: 8,
          width: 28, height: 28, borderRadius: '50%',
          border: '1px solid #ccc', background: 'rgba(255,255,255,0.9)',
          cursor: 'pointer', fontSize: 14, lineHeight: 1,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
        }}
      >ⓘ</button>

      {showLegend && (
        <div style={{
          position: 'absolute', top: 42, right: 8,
          background: 'rgba(255,255,255,0.95)', borderRadius: 6,
          padding: '6px 10px', fontSize: 11, lineHeight: 1.8,
          boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
          pointerEvents: 'none',
        }}>
          {TYPE_ORDER.map((type) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: TYPE_COLOR[type], display: 'inline-block' }} />
              {TYPE_KO[type]}
            </div>
          ))}
        </div>
      )}

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
