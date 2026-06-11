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

// 노드 타입 팔레트 — MapView 지도와 통일: 장소=지도 related-place 파랑, 사건=지도 주황.
// 인물=앱 보라 액센트, 집단=청록, 기타=회색.
const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Unknown']
const TYPE_KO = { Person: '인물', Place: '장소', Event: '사건', PeopleGroup: '집단', Unknown: '기타' }
const TYPE_COLOR = { Person: '#7c9cfc', Place: '#4a90d9', Event: '#f5a623', PeopleGroup: '#2bb6a8', Unknown: '#9aa5b8' }

function typeOf(label) {
  return TYPE_COLOR[label] ? label : 'Unknown'
}

function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false }) {
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

  const msgStyle = { padding: '1.25rem', fontSize: 14, color: '#7c8db0' }
  if (!nodeId) return <p style={msgStyle}>지도에서 마커를 클릭하세요</p>
  if (!ready) return <p style={msgStyle}>로딩 중...</p>
  if (error) return <p style={{ ...msgStyle, color: '#dc3545' }}>불러오지 못했습니다 ({error})</p>

  // 이웃을 타입별로 그룹
  const groups = {}
  for (const n of node.neighbors) {
    const t = typeOf(n.label)
    if (!groups[t]) groups[t] = []
    groups[t].push(n)
  }

  const title = node.nameKoMissing ? `${node.name} (미번역)` : node.nameKo
  const subtitle = [
    !node.nameKoMissing && node.name !== node.nameKo ? node.name : null,
    TYPE_KO[node.label] || node.label,
  ].filter(Boolean).join(' · ')
  const headColor = TYPE_COLOR[typeOf(node.label)]

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* 헤더 */}
      <div style={{
        padding: '14px 44px 14px 16px',
        borderBottom: '1px solid #eef0f5',
        position: 'sticky', top: 0, background: 'white', zIndex: 1,
      }}>
        {canGoBack && (
          <button
            onClick={onBack}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              border: 'none', background: 'none', cursor: 'pointer',
              color: '#7c8db0', fontSize: 13, padding: 0, marginBottom: 8, font: 'inherit',
            }}
          >← 뒤로</button>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: headColor, flexShrink: 0 }} />
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#1a1a2e', lineHeight: 1.3 }}>{title}</h2>
        </div>
        <div style={{ fontSize: 12, color: '#7c8db0', marginTop: 3, marginLeft: 18 }}>{subtitle}</div>
      </div>

      {/* 이웃 그룹 */}
      <div style={{ padding: '4px 12px 20px' }}>
        {node.neighbors.length === 0 && (
          <p style={{ color: '#7c8db0', fontSize: 13, padding: '12px 4px' }}>연결된 이웃이 없습니다</p>
        )}
        {TYPE_ORDER.filter(t => groups[t]?.length).map(t => (
          <div key={t} style={{ marginTop: 14 }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              fontSize: 12, fontWeight: 700, color: TYPE_COLOR[t], padding: '0 4px 6px',
            }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: TYPE_COLOR[t] }} />
              {TYPE_KO[t]}
              <span style={{ color: '#aab2c5', fontWeight: 500 }}>{groups[t].length}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {groups[t].map(n => (
                <button
                  key={n.id + ':' + n.relation}
                  onClick={() => onSelectNode(n.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    width: '100%', textAlign: 'left', font: 'inherit',
                    border: 'none', background: 'none', cursor: 'pointer',
                    borderLeft: `3px solid ${TYPE_COLOR[t]}`,
                    borderRadius: 6, padding: '8px 10px',
                    transition: 'background 0.12s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = '#f4f6fb' }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                >
                  <span style={{ flex: 1, fontSize: 14, color: '#1a1a2e' }}>
                    {n.nameKoMissing ? `${n.name} (미번역)` : n.nameKo}
                  </span>
                  <span style={{
                    fontSize: 10, color: '#7c8db0', background: '#eef0f5',
                    borderRadius: 4, padding: '2px 6px', flexShrink: 0,
                  }}>{REL_KO[n.relation] || n.relation}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SidePanel
