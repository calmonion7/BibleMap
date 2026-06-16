import { useState, useEffect } from 'react'
import { TYPE_COLOR, TYPE_KO } from './theme'
import { apiGet } from './api'
import { fetchChapter } from './getbible'

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
// 장(chapter) JSON을 받아 verses[]에서 해당 절을 찾는다(getbible.js fetchChapter로 장 캐시 공유).
async function fetchVerseText(bookOrder, chapter, verse) {
  const d = await fetchChapter(bookOrder, chapter)
  return d?.verses?.find(v => v.verse === verse)?.text || null
}

// "창 1:1" 형태에서 chapter, verse 추출. 범위(6:4-5)는 첫 절만 사용.
function parseVerseRef(ref) {
  if (!ref) return null
  const m = ref.match(/(\d+):(\d+)/)
  if (!m) return null
  return { chapter: parseInt(m[1]), verse: parseInt(m[2]) }
}

// 개역 약어 → getbible 책 번호(canonical 1~66). trait verse_ref 원문 fetch용.
const BOOK_ABBR_ORDER = {
  '창': 1, '출': 2, '레': 3, '민': 4, '신': 5, '수': 6, '삿': 7, '룻': 8,
  '삼상': 9, '삼하': 10, '왕상': 11, '왕하': 12, '대상': 13, '대하': 14, '스': 15, '느': 16,
  '에': 17, '욥': 18, '시': 19, '잠': 20, '전': 21, '아': 22, '사': 23, '렘': 24,
  '애': 25, '겔': 26, '단': 27, '호': 28, '욜': 29, '암': 30, '옵': 31, '욘': 32,
  '미': 33, '나': 34, '합': 35, '습': 36, '학': 37, '슥': 38, '말': 39, '마': 40,
  '막': 41, '눅': 42, '요': 43, '행': 44, '롬': 45, '고전': 46, '고후': 47, '갈': 48,
  '엡': 49, '빌': 50, '골': 51, '살전': 52, '살후': 53, '딤전': 54, '딤후': 55, '딛': 56,
  '몬': 57, '히': 58, '약': 59, '벧전': 60, '벧후': 61, '요일': 62, '요이': 63, '요삼': 64,
  '유': 65, '계': 66,
}

// "창 15:6" / "창 6:4-5"에서 책 약어 + chapter + 첫 verse를 bookOrder로 해석. 매핑 불가 시 null.
function resolveVerseRef(ref) {
  if (!ref) return null
  const m = ref.match(/^\s*([^\d\s]+)\s*(\d+):(\d+)/)
  if (!m) return null
  const bookOrder = BOOK_ABBR_ORDER[m[1]]
  if (!bookOrder) return null
  return { bookOrder, chapter: parseInt(m[2]), verse: parseInt(m[3]) }
}

// collapsed[key] !== false → 접힘(기본), false → 펼침
function SectionHeader({ label, color, count, sectionKey, collapsed, onToggle }) {
  const isOpen = collapsed[sectionKey] === false
  return (
    <button
      onClick={() => onToggle(sectionKey)}
      style={{
        display: 'flex', alignItems: 'center', gap: 6, width: '100%',
        border: 'none', background: 'none', cursor: 'pointer', padding: '0 4px 6px',
        fontSize: 12, fontWeight: 700, color: color ?? '#5a6481',
      }}
    >
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <span style={{ flex: 1, textAlign: 'left' }}>{label}</span>
      {count != null && <span style={{ color: '#aab2c5', fontWeight: 500 }}>{count}</span>}
      <span style={{ fontSize: 10, color: '#aab2c5', marginLeft: 2 }}>{isOpen ? '▾' : '▸'}</span>
    </button>
  )
}

function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false, onNodeLoaded }) {
  // 어느 nodeId의 결과인지 id로 추적 — loading은 파생, stale 응답은 무시.
  // setState는 비동기 콜백에서만 호출(react-hooks set-state-in-effect 준수).
  const [state, setState] = useState({ id: null, node: null, error: null })
  // keyVerse는 어느 nodeId의 결과인지 id로 묶어 stale 표시를 방지(동기 reset 불필요).
  const [keyVerseState, setKeyVerseState] = useState({ id: null, text: null })
  const [collapsed, setCollapsed] = useState({})
  // trait 원문 캐시 — verse_ref로 키잉(노드 무관, 동일 구절 재fetch 방지·stale 안전). { ref: { status, text } }
  const [traitVerses, setTraitVerses] = useState({})

  useEffect(() => {
    if (!nodeId) return
    let cancelled = false
    apiGet('/node/' + nodeId)
      .then(data => { if (!cancelled) { setCollapsed({}); setState({ id: nodeId, node: data, error: null }); onNodeLoaded?.(data) } })
      .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: String(e) }) })
    return () => { cancelled = true }
  }, [nodeId, onNodeLoaded])

  // Book keyVerse 텍스트 외부 API fetch (결과를 nodeId로 묶어 저장 — 렌더에서 현재 노드일 때만 사용)
  useEffect(() => {
    const node = state.id === nodeId ? state.node : null
    if (!node || node.label !== 'Book') return
    const bookOrder = node.properties?.bookOrder
    const keyVerse = node.properties?.keyVerse
    if (!bookOrder || !keyVerse) return
    const parsed = parseVerseRef(keyVerse)
    if (!parsed) return
    let cancelled = false
    fetchVerseText(bookOrder, parsed.chapter, parsed.verse).then(text => {
      if (!cancelled) setKeyVerseState({ id: nodeId, text })
    })
    return () => { cancelled = true }
  }, [state, nodeId])

  const ready = state.id === nodeId
  const node = ready ? state.node : null
  const error = ready ? state.error : null
  // 현재 노드의 keyVerse만 사용(이전 Book의 stale 텍스트 무시)
  const keyVerseText = keyVerseState.id === nodeId ? keyVerseState.text : null

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

  function toggle(key) {
    setCollapsed(prev => ({ ...prev, [key]: prev[key] === false }))
  }

  // trait 원문 펼침/접힘 + 펼칠 때 lazy fetch(미캐시 시 1회).
  function toggleTraitVerse(i, ref) {
    const key = 'trait-' + i
    const opening = collapsed[key] !== false
    toggle(key)
    if (!opening || !ref || traitVerses[ref] !== undefined) return
    const parsed = resolveVerseRef(ref)
    if (!parsed) {
      setTraitVerses(prev => ({ ...prev, [ref]: { status: 'error' } }))
      return
    }
    setTraitVerses(prev => ({ ...prev, [ref]: { status: 'loading' } }))
    fetchVerseText(parsed.bookOrder, parsed.chapter, parsed.verse).then(text => {
      setTraitVerses(prev => ({ ...prev, [ref]: text ? { status: 'done', text } : { status: 'error' } }))
    })
  }

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

      {/* Person 인물 성품 섹션 — 이웃 그룹보다 위 */}
      {node.label === 'Person' && node.properties?.traits?.length > 0 && (
        <div style={{
          margin: '12px 12px 0', padding: '12px', borderRadius: 8,
          background: '#f8faff', border: '1px solid #e8ecf8',
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Person, marginBottom: 10 }}>
            인물 성품
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {node.properties.traits.map((t, i) => {
              const open = collapsed['trait-' + i] === false
              const v = traitVerses[t.verse_ref]
              return (
              <div key={i}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600, color: '#1a1a2e',
                    background: 'rgba(124,156,252,0.12)', borderRadius: 4, padding: '2px 8px',
                  }}>{t.trait}</span>
                  <button
                    onClick={() => toggleTraitVerse(i, t.verse_ref)}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 3,
                      border: 'none', background: 'none', cursor: 'pointer', padding: 0,
                      font: 'inherit', fontSize: 10, color: '#9aa5b8',
                    }}
                  >
                    {t.verse_ref}
                    <span style={{ fontSize: 9 }}>{open ? '▾' : '▸'}</span>
                  </button>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#5a6481', lineHeight: 1.5 }}>{t.description}</p>
                {open && (
                  <div style={{
                    marginTop: 5, padding: '7px 10px', background: '#eef2ff',
                    borderLeft: `3px solid ${TYPE_COLOR.Person}`, borderRadius: 6,
                    fontSize: 12, color: '#374151', lineHeight: 1.5,
                  }}>
                    {v?.status === 'done'
                      ? v.text
                      : <span style={{ color: '#9aa5b8' }}>
                          {v?.status === 'loading' ? '불러오는 중…' : '원문을 불러오지 못했습니다'}
                        </span>}
                  </div>
                )}
              </div>
              )
            })}
          </div>
        </div>
      )}

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
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="시대적 배경" color="#a78bfa" sectionKey="book-background" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-background'] === false && (
                <p style={{ margin: '0 0 4px', color: '#374151', lineHeight: 1.6 }}>{node.properties.background}</p>
              )}
            </div>
          )}

          {/* 성경 주제 */}
          {node.properties.themes?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="핵심 주제" color="#a78bfa" sectionKey="book-themes" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-themes'] === false && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', paddingBottom: 4 }}>
                  {node.properties.themes.map((t, i) => (
                    <span key={i} style={{
                      fontSize: 12, padding: '4px 10px', borderRadius: 999,
                      border: '1px solid #a78bfa', color: '#a78bfa',
                    }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 대표 구절 */}
          {node.properties.keyVerse && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="대표 구절" color="#a78bfa" sectionKey="book-keyverse" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-keyverse'] === false && (
                <div style={{
                  padding: '10px 12px', background: '#f5f3ff', borderRadius: 8,
                  borderLeft: '3px solid #a78bfa', marginBottom: 4,
                }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#6d28d9', marginBottom: keyVerseText ? 4 : 0 }}>
                    {node.properties.keyVerse}
                  </div>
                  {keyVerseText && (
                    <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{keyVerseText}</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 주요 인물 */}
          {node.topPersons?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <SectionHeader label="주요 인물" color={TYPE_COLOR.Person} count={node.topPersons.length} sectionKey="book-persons" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-persons'] === false && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingBottom: 4 }}>
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
              )}
            </div>
          )}

          {/* 주요 사건 */}
          {node.topEvents?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <SectionHeader label="주요 사건" color={TYPE_COLOR.Event} count={node.topEvents.length} sectionKey="book-events" collapsed={collapsed} onToggle={toggle} />
              {collapsed['book-events'] === false && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingBottom: 4 }}>
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
              )}
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
            <SectionHeader label={TYPE_KO[t] || t} color={TYPE_COLOR[t] || TYPE_COLOR.Unknown} count={groups[t].length} sectionKey={t} collapsed={collapsed} onToggle={toggle} />
            {collapsed[t] === false && (
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
            )}
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
    </div>
  )
}

export default SidePanel
