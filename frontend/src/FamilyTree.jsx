import { useState, useEffect, useMemo, useRef, useLayoutEffect } from 'react'
import { TYPE_COLOR } from './theme'
import { apiGet } from './api'
import Spinner from './Spinner'

// 인물 중심(ego-centric) 가계도 — 그래프 혈통 파생(ADR-0019).
// 위로 조상선 완전 펼침, 아래로 자손 2세대, focus 행에 형제·배우자 인라인.
// 노드 클릭 시 onRecenter(id)로 재중심화. 손수 SVG 커넥터 + 절대배치 세대 레이아웃(라이브러리 없음).

const ROW_H = 88
const CHIP_W = 108
const CHIP_H = 46
const COL_W = 132  // CHIP_W + 좌우 여백

// 서브그래프 → 세대·좌표 레이아웃 계산.
function computeLayout(data) {
  const { focus, nodes, parentEdges, siblings = [], partners = [] } = data
  const byId = Object.fromEntries(nodes.map(n => [n.id, n]))
  if (!byId[focus]) return null

  // 세대: focus=0, 조상 양수(위), 자손 음수(아래). DAG 완화(relaxation)로 병합 정렬.
  const gen = { [focus]: 0 }
  let changed = true
  while (changed) {  // 조상: 부모 = 자식 + 1 (가장 깊은 값 유지 → 병합 정렬)
    changed = false
    for (const [p, c] of parentEdges) {
      if (gen[c] !== undefined && gen[c] >= 0) {
        const g = gen[c] + 1
        if (gen[p] === undefined || gen[p] < g) { gen[p] = g; changed = true }
      }
    }
  }
  changed = true
  while (changed) {  // 자손: 자식 = 부모 - 1 (가장 낮은 값 유지)
    changed = false
    for (const [p, c] of parentEdges) {
      if (gen[p] !== undefined && gen[p] <= 0) {
        const g = gen[p] - 1
        if (gen[c] === undefined || gen[c] > g) { gen[c] = g; changed = true }
      }
    }
  }
  // 형제·배우자와 미배치 노드는 focus 행(0)에.
  const sibSet = new Set(siblings), partSet = new Set(partners)
  for (const n of nodes) if (gen[n.id] === undefined) gen[n.id] = 0

  // 세대별 그룹 + 행 내 정렬(형제 · focus · 배우자 순으로 focus 행 배치).
  const byGen = {}
  for (const n of nodes) (byGen[gen[n.id]] ??= []).push(n.id)
  const focusRow = byGen[0] || []
  byGen[0] = [
    ...focusRow.filter(id => sibSet.has(id)),
    ...focusRow.filter(id => id === focus),
    ...focusRow.filter(id => !sibSet.has(id) && !partSet.has(id) && id !== focus),
    ...focusRow.filter(id => partSet.has(id)),
  ]

  const gens = Object.keys(byGen).map(Number)
  const maxGen = Math.max(...gens), minGen = Math.min(...gens)
  const maxCols = Math.max(...gens.map(g => byGen[g].length))
  const totalW = Math.max(maxCols, 1) * COL_W
  const totalH = (maxGen - minGen + 1) * ROW_H

  const pos = {}
  for (const g of gens) {
    const row = byGen[g]
    const startX = (totalW - row.length * COL_W) / 2
    row.forEach((id, i) => {
      pos[id] = { x: startX + i * COL_W + (COL_W - CHIP_W) / 2, y: (maxGen - g) * ROW_H }
    })
  }
  return { byId, pos, gen, parentEdges, totalW, totalH, focus, sibSet, partSet, roles: data.roles || {} }
}

// 칩 역할 라벨 — 큐레이션 정본 role(맏아들·둘째 아들 등)이 있으면 그대로, 없으면 그래프 구조 + gender 폴백.
// 첫째/둘째 순서는 정본에만 있고(theographic children 비정렬), 폴백은 성별 kinship까지만.
function roleLabel(id, layout) {
  if (layout.roles[id]) return layout.roles[id]
  if (id === layout.focus) return null
  const g = layout.gen[id]
  const gender = layout.byId[id]?.gender
  const M = gender === 'Male', F = gender === 'Female'
  if (layout.partSet.has(id)) return M ? '남편' : F ? '아내' : '배우자'
  if (layout.sibSet.has(id)) return M ? '형제' : F ? '자매' : '형제자매'
  if (g < 0) return g === -1 ? (M ? '아들' : F ? '딸' : '자녀') : g === -2 ? (M ? '손자' : F ? '손녀' : '손주') : '후손'
  if (g > 0) return g === 1 ? (M ? '아버지' : F ? '어머니' : '부모') : g === 2 ? (M ? '조부' : F ? '조모' : '조부모') : '조상'
  return null
}

function FamilyTree({ personId, onRecenter = () => {}, onOpenPerson = () => {} }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const scrollRef = useRef(null)

  useEffect(() => {
    const ctrl = new AbortController()
    setLoading(true)
    apiGet(`/person/${personId}/family`, { signal: ctrl.signal })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[FamilyTree] 가계도 로드 실패', e); setData(null); setLoading(false) } })
    return () => ctrl.abort()
  }, [personId])

  const layout = useMemo(() => (data ? computeLayout(data) : null), [data])

  // 에고뷰: 렌더 후 focus 인물이 화면에 오도록 스크롤(조상선이 길어 focus가 하단에 있을 때 필수).
  useLayoutEffect(() => {
    const el = scrollRef.current
    if (!el || !layout) return
    const f = layout.pos[layout.focus]
    if (!f) return
    el.scrollTop = Math.max(0, f.y - el.clientHeight * 0.4)
    el.scrollLeft = Math.max(0, f.x + CHIP_W / 2 - el.clientWidth / 2)
  }, [layout])

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}><Spinner /></div>
  if (!layout || (data && data.nodes.length <= 1)) {
    const name = data?.nodes?.find(n => n.id === personId)?.nameKo
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--ink-faint)', fontSize: 14 }}>
        {name ? `${name}의 ` : ''}혈통 정보가 없습니다.
      </div>
    )
  }

  const { byId, pos, parentEdges, totalW, totalH, focus } = layout
  const focusNode = byId[focus]

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg-0)' }}>
      {/* focus 인물 액션 바 — 인물 페이지(탐험)로 바로가기. 다른 인물은 노드 클릭으로 재중심화 후 이동. */}
      {focusNode && (
        <div style={{
          flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
          padding: '8px 14px', borderBottom: '1px solid var(--line)', background: 'var(--bg-1)',
        }}>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: 'var(--gold)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {focusNode.nameKo}
          </span>
          <button
            onClick={() => onOpenPerson(focus)}
            style={{
              flexShrink: 0, display: 'flex', alignItems: 'center', gap: 5,
              padding: '7px 12px', borderRadius: 8, cursor: 'pointer', font: 'inherit',
              fontSize: 12.5, fontWeight: 600, color: 'var(--gold)',
              background: 'var(--bg-2)', border: '1px solid var(--line-strong)',
            }}
          >
            인물 페이지 →
          </button>
        </div>
      )}
      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto' }}>
      <div style={{ position: 'relative', width: totalW, height: totalH, margin: '24px auto 48px', minWidth: '100%' }}>
        {/* 커넥터 — 부모(하단중앙) → 자식(상단중앙) */}
        <svg width={totalW} height={totalH} style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
          {parentEdges.map(([p, c], i) => {
            const pp = pos[p], pc = pos[c]
            if (!pp || !pc) return null
            const x1 = pp.x + CHIP_W / 2, y1 = pp.y + CHIP_H
            const x2 = pc.x + CHIP_W / 2, y2 = pc.y
            const midY = (y1 + y2) / 2
            return (
              <path key={i} d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
                fill="none" stroke="var(--line-strong)" strokeWidth={1.5} />
            )
          })}
        </svg>

        {/* 인물 칩 */}
        {Object.entries(pos).map(([id, p]) => {
          const n = byId[id]
          if (!n) return null
          const isFocus = id === focus
          const tag = roleLabel(id, layout)
          return (
            <button
              key={id}
              onClick={() => { if (!isFocus) onRecenter(id) }}
              title={n.nameKo}
              style={{
                position: 'absolute', left: p.x, top: p.y,
                width: CHIP_W, height: CHIP_H,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1,
                padding: '2px 6px', borderRadius: 8,
                border: isFocus ? '2px solid var(--gold)' : '1px solid var(--line-strong)',
                background: isFocus ? 'var(--bg-2)' : 'var(--bg-1)',
                color: 'var(--ink)', font: 'inherit',
                fontFamily: 'var(--serif)', fontSize: 13, fontWeight: isFocus ? 700 : 500,
                cursor: isFocus ? 'default' : 'pointer',
                boxShadow: 'var(--shadow-1)',
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}
            >
              <span style={{ maxWidth: '100%', overflow: 'hidden', textOverflow: 'ellipsis' }}>{n.nameKo}</span>
              {tag && <span style={{ fontSize: 9, fontFamily: 'system-ui', color: 'var(--ink-faint)', fontWeight: 400 }}>{tag}</span>}
              {n.authored && <span title="저작 보충" style={{ position: 'absolute', top: 3, right: 4, width: 5, height: 5, borderRadius: '50%', background: TYPE_COLOR.Person }} />}
            </button>
          )
        })}
      </div>
      </div>
    </div>
  )
}

export default FamilyTree
