import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function SidePanel({ nodeId, onSelectNode = () => {} }) {
  const [node, setNode] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!nodeId) {
      setNode(null)
      return
    }
    setLoading(true)
    setError(null)
    fetch(API_URL + '/node/' + nodeId)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => { setNode(data); setLoading(false) })
      .catch(e => { setError(String(e)); setLoading(false) })
  }, [nodeId])

  if (!nodeId) return <p style={{ padding: '1rem' }}>지도에서 마커를 클릭하세요</p>
  if (loading || !node) return <p>로딩 중...</p>
  if (error) return <p>오류: {error}</p>

  return (
    <div style={{ padding: '1rem' }}>
      <h2>{node.nameKoMissing ? node.name + ' (미번역)' : node.nameKo + ' (' + node.name + ')'}</h2>
      <h3>이웃</h3>
      <ul>
        {node.neighbors.map(n => (
          <li key={n.id}>
            <button
              style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'inherit', padding: 0, font: 'inherit', textAlign: 'left' }}
              onClick={() => onSelectNode(n.id)}
            >
              {n.nameKoMissing ? n.name + ' (미번역)' : n.nameKo + ' (' + n.name + ')'} [{n.relation}]
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default SidePanel
