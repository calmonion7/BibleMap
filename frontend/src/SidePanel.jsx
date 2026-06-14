import { useState, useEffect } from 'react'
import { TYPE_COLOR, TYPE_KO } from './theme'

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

// 이웃 그룹핑 표시 순서(Unknown 포함 — 미매핑 타입도 묶는다). 색·한글 라벨은 theme.js 공유 팔레트.
const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Unknown']

function typeOf(label) {
  return TYPE_COLOR[label] ? label : 'Unknown'
}

// 외부 한국어 성경 API로 구절 텍스트 fetch. 실패 시 null 반환.
async function fetchVerseText(bookOrder, chapter, verse) {
  try {
    const url = `https://api.getbible.net/v2/kor/${bookOrder}/${chapter}/${verse}.json`
    const r = await fetch(url)
    if (!r.ok) return null
    const d = await r.json()
    return d.verse || null
  } catch {
    return null
  }
}

// "창 1:1" 형태에서 chapter, verse 추출. 범위(6:4-5)는 첫 절만 사용.
function parseVerseRef(ref) {
  if (!ref) return null
  const m = ref.match(/(\d+):(\d+)/)
  if (!m) return null
  return { chapter: parseInt(m[1]), verse: parseInt(m[2]) }
}

function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false }) {
  // 어느 nodeId의 결과인지 id로 추적 — loading은 파생, stale 응답은 무시.
  // setState는 비동기 콜백에서만 호출(react-hooks set-state-in-effect 준수).
  const [state, setState] = useState({ id: null, node: null, error: null })
  const [keyVerseText, setKeyVerseText] = useState(null)

  useEffect(() => {
    if (!nodeId) return
    let cancelled = false
    fetch(API_URL + '/node/' + nodeId)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => { if (!cancelled) setState({ id: nodeId, node: data, error: null }) })
      .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: String(e) }) })
    return () => { cancelled = true }
  }, [nodeId])

  // Book keyVerse 텍스트 외부 API fetch
  useEffect(() => {
    setKeyVerseText(null)
    const node = state.id === nodeId ? state.node : null
    if (!node || node.label !== 'Book') return
    const bookOrder = node.properties?.bookOrder
    const keyVerse = node.properties?.keyVerse
    if (!bookOrder || !keyVerse) return
    const parsed = parseVerseRef(keyVerse)
    if (!parsed) return
    let cancelled = false
    fetchVerseText(bookOrder, parsed.chapter, parsed.verse).then(text => {
      if (!cancelled) setKeyVerseText(text)
    })
    return () => { cancelled = true }
  }, [state, nodeId])

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

      {/* Book 전용 뷰 */}
      {node.label === 'Book' && (
        <div style={{ padding: '12px 16px 20px', fontSize: 14 }}>
          {/* 메타 칩 */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
            {[node.properties.testament, node.properties.genre,
              node.properties.startYear && `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC`,
              node.properties.chapterCount && `${node.properties.chapterCount}장`]
              .filter(Boolean).map((chip, i) => (
              <span key={i} style={{
                fontSize: 11, padding: '3px 8px', borderRadius: 999,
                background: '#eef0f5', color: '#5a6481',
              }}>{chip}</span>
            ))}
          </div>

          {/* 시대적 배경 */}
          {node.properties.background && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#a78bfa', marginBottom: 6 }}>시대적 배경</div>
              <p style={{ margin: 0, color: '#374151', lineHeight: 1.6 }}>{node.properties.background}</p>
            </div>
          )}

          {/* 성경 주제 */}
          {node.properties.themes?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#a78bfa', marginBottom: 6 }}>핵심 주제</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {node.properties.themes.map((t, i) => (
                  <span key={i} style={{
                    fontSize: 12, padding: '4px 10px', borderRadius: 999,
                    border: '1px solid #a78bfa', color: '#a78bfa',
                  }}>{t}</span>
                ))}
              </div>
            </div>
          )}

          {/* 대표 구절 */}
          {node.properties.keyVerse && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#a78bfa', marginBottom: 6 }}>대표 구절</div>
              <div style={{
                padding: '10px 12px', background: '#f5f3ff', borderRadius: 8,
                borderLeft: '3px solid #a78bfa',
              }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#6d28d9', marginBottom: keyVerseText ? 4 : 0 }}>
                  {node.properties.keyVerse}
                </div>
                {keyVerseText && (
                  <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{keyVerseText}</div>
                )}
              </div>
            </div>
          )}

          {/* 주요 인물 */}
          {node.topPersons?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Person, marginBottom: 6 }}>
                주요 인물
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {node.topPersons.map(p => (
                  <button key={p.id} onClick={() => onSelectNode(p.id)} style={{
                    display: 'flex', alignItems: 'center',
                    width: '100%', textAlign: 'left', font: 'inherit',
                    border: 'none', background: 'none', cursor: 'pointer',
                    borderLeft: `3px solid ${TYPE_COLOR.Person}`,
                    borderRadius: 6, padding: '7px 10px',
                    transition: 'background 0.12s',
                  }}
                    onMouseEnter={e => { e.currentTarget.style.background = '#f4f6fb' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                  >
                    <span style={{ fontSize: 13, color: '#1a1a2e' }}>{p.nameKo || p.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 주요 사건 */}
          {node.topEvents?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Event, marginBottom: 6 }}>
                주요 사건
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {node.topEvents.map(e => (
                  <button key={e.id} onClick={() => onSelectNode(e.id)} style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    width: '100%', textAlign: 'left', font: 'inherit',
                    border: 'none', background: 'none', cursor: 'pointer',
                    borderLeft: `3px solid ${TYPE_COLOR.Event}`,
                    borderRadius: 6, padding: '7px 10px',
                    transition: 'background 0.12s',
                  }}
                    onMouseEnter={ev => { ev.currentTarget.style.background = '#f4f6fb' }}
                    onMouseLeave={ev => { ev.currentTarget.style.background = 'none' }}
                  >
                    <span style={{ flex: 1, fontSize: 13, color: '#1a1a2e' }}>{e.nameKo || e.name}</span>
                    {e.startDate && (
                      <span style={{ fontSize: 10, color: '#9aa5b8', flexShrink: 0 }}>
                        {e.startDate < 0 ? `BC ${Math.abs(e.startDate)}` : `AD ${e.startDate}`}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 이웃 그룹 (Book 제외) */}
      {node.label !== 'Book' && (
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
        {node.neighborTotal > node.neighbors.length && (
          <p style={{
            color: '#aab2c5', fontSize: 12, padding: '12px 6px 0',
            borderTop: '1px solid #eef0f5', marginTop: 14,
          }}>
            이웃 {node.neighborTotal}개 중 {node.neighbors.length}개 표시
          </p>
        )}
      </div>
      )}

      {/* Person 인물 성품 섹션 */}
      {node.label === 'Person' && node.properties?.traits?.length > 0 && (
        <div style={{
          margin: '0 12px 20px', padding: '12px', borderRadius: 8,
          background: '#f8faff', border: '1px solid #e8ecf8',
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Person, marginBottom: 10 }}>
            인물 성품
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {node.properties.traits.map((t, i) => (
              <div key={i}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600, color: '#1a1a2e',
                    background: 'rgba(124,156,252,0.12)', borderRadius: 4, padding: '2px 8px',
                  }}>{t.trait}</span>
                  <span style={{ fontSize: 10, color: '#9aa5b8' }}>{t.verse_ref}</span>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#5a6481', lineHeight: 1.5 }}>{t.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SidePanel
