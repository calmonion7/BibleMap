import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const REL_KO = {
  PARENT_OF: '부모',
  CHILD_OF: '자녀',
  SIBLING_OF: '형제·자매',
  PARTNER_OF: '배우자',
  MEMBER_OF: '소속',
  HAS_PARTICIPANT: '참여',
  OCCURS_AT: '발생 장소',
  PART_OF: '상위 사건',
}

function SidePanel({ nodeId, onSelectNode = () => {} }) {
  // 어느 nodeId의 결과인지 id로 추적 — loading은 파생, stale 응답은 무시.
  // setState는 비동기 콜백에서만 호출(react-hooks set-state-in-effect 준수).
  const [state, setState] = useState({ id: null, node: null, error: null })

  useEffect(() => {
    if (!nodeId) return
    let cancelled = false
    fetch(API_URL + '/node/' + nodeId)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => { if (!cancelled) setState({ id: nodeId, node: data, error: null }) })
      .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: String(e) }) })
    return () => { cancelled = true }
  }, [nodeId])

  const ready = state.id === nodeId
  const node = ready ? state.node : null
  const error = ready ? state.error : null

  if (!nodeId) return <p style={{ padding: '1rem' }}>지도에서 마커를 클릭하세요</p>
  if (!ready) return <p>로딩 중...</p>
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
              {n.nameKoMissing ? n.name + ' (미번역)' : n.nameKo + ' (' + n.name + ')'} [{REL_KO[n.relation] || n.relation}]
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default SidePanel
