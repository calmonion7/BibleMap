import { useState, useEffect, useMemo, useRef, useLayoutEffect } from 'react'
import { TYPE_COLOR } from './theme'
import { apiGet } from './api'
import Spinner from './Spinner'
import PersonSymbol, { hasSymbol } from './personSymbols'
import PersonMiniCard from './PersonMiniCard'

// 인물 중심(ego-centric) 가계도 — 그래프 혈통 파생(ADR-0019), 구조 개편(task#196).
// 위로 조상선: 앵커(인장 보유 + focus 직계 3세대) 행만 노출, 비앵커 구간은 "…N대" 접힌
// 세그먼트 칩(탭 시 인라인 펼침). focus 행: 형제·배우자 인라인(줄바꿈). 아래 자식 세대:
// 어머니 그룹 컨테이너(그룹당 커넥터 1개, 칩 줄바꿈), 손주는 그룹별 요약 칩으로 축약.
// 노드 3계층: focus 큰 카드(인장+serif+role+gold 보더) · 앵커 칩(미니 인장+serif) · 일반 소형 칩.
// 레이아웃은 DOM 플로우(flex wrap — 모바일 가로 넘침 원천 제거), 커넥터는 렌더 후 측정한 SVG.

const ANCHOR_GEN = 3 // focus 직계 3세대는 무조건 노출

// 서브그래프 → 세대·섹션 모델 계산.
function buildModel(data) {
  const { focus, nodes, parentEdges, siblings = [], partners = [], mothers = {} } = data
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

  const sibSet = new Set(siblings), partSet = new Set(partners)

  // 조상 행(위→아래 = 오래된 세대→부모): 계보(lineage) 노드 우선 정렬로 사슬 시각 연속성 확보.
  const byGen = {}
  for (const n of nodes) {
    const g = gen[n.id]
    if (g !== undefined && g > 0) (byGen[g] ??= []).push(n.id)
  }
  const maxGen = Math.max(0, ...Object.keys(byGen).map(Number))
  for (const g of Object.keys(byGen)) {
    byGen[g].sort((a, b) => (byId[b].lineage === true) - (byId[a].lineage === true))
  }

  // 앵커 행 판정 + 비앵커 연속 구간 → 접힌 세그먼트
  const rows = [] // 위(오래된)→아래(부모): {type:'gen', g, ids} | {type:'segment', id, gens:[...]}
  let run = []
  const flushRun = () => {
    if (run.length) {
      // 메시아의 실이 지나가는 접힌 구간은 금 점선으로 표시(task#197)
      const lineage = run.some(g => (byGen[g] || []).some(id => byId[id].lineage))
      rows.push({ type: 'segment', id: `seg-${run[0]}`, gens: [...run], lineage })
      run = []
    }
  }
  for (let g = maxGen; g >= 1; g--) {
    const ids = byGen[g] || []
    if (!ids.length) continue
    const isAnchorRow = g <= ANCHOR_GEN || ids.some(id => hasSymbol(byId[id].slug))
    if (isAnchorRow) { flushRun(); rows.push({ type: 'gen', g, ids }) }
    else run.push(g)
  }
  flushRun()

  // focus 행: 형제 · focus · 배우자 (+ 세대 미배정 잔여 노드 — 어머니 라벨 전용 등)
  const placed = new Set([focus, ...Object.keys(byGen).flatMap(g => byGen[g])])
  const focusRow = {
    siblings: nodes.filter(n => sibSet.has(n.id)).map(n => n.id),
    partners: nodes.filter(n => (partSet.has(n.id) || (gen[n.id] === undefined && !sibSet.has(n.id))) && n.id !== focus)
      .filter(n => gen[n.id] === undefined || gen[n.id] === 0)
      .map(n => n.id),
  }
  focusRow.siblings.forEach(id => placed.add(id))
  focusRow.partners.forEach(id => placed.add(id))

  // 자식 세대(gen -1) → 어머니 그룹. 어머니 그룹 순서: 라벨 있는 그룹(어머니 이름순) → 미상 그룹.
  const children = nodes.filter(n => gen[n.id] === -1).map(n => n.id)
  const groupsByMother = new Map()
  for (const cid of children) {
    const mid = mothers[cid] || null
    if (!groupsByMother.has(mid)) groupsByMother.set(mid, [])
    groupsByMother.get(mid).push(cid)
  }
  const groups = [...groupsByMother.entries()]
    .map(([motherId, ids]) => ({ motherId, ids }))
    .sort((a, b) => {
      if (!a.motherId) return 1
      if (!b.motherId) return -1
      return (byId[a.motherId]?.nameKo || '').localeCompare(byId[b.motherId]?.nameKo || '')
    })

  // 손주(gen -2): 자식별 목록
  const grandchildren = {}
  for (const [p, c] of parentEdges) {
    if (gen[c] === -2 && gen[p] === -1) (grandchildren[p] ??= []).push(c)
  }

  return { byId, gen, rows, focusRow, groups, grandchildren, parentEdges, focus, sibSet, partSet, roles: data.roles || {} }
}

// 칩 역할 라벨 — 큐레이션 정본 role(맏아들·둘째 아들 등)이 있으면 그대로, 없으면 그래프 구조 + gender 폴백.
function roleLabel(id, model) {
  if (model.roles[id]) return model.roles[id]
  if (id === model.focus) return null
  const g = model.gen[id]
  const gender = model.byId[id]?.gender
  const M = gender === 'Male', F = gender === 'Female'
  if (model.partSet.has(id)) return M ? '남편' : F ? '아내' : '배우자'
  if (model.sibSet.has(id)) return M ? '형제' : F ? '자매' : '형제자매'
  if (g === undefined) return null
  if (g < 0) return g === -1 ? (M ? '아들' : F ? '딸' : '자녀') : g === -2 ? (M ? '손자' : F ? '손녀' : '손주') : '후손'
  if (g > 0) return g === 1 ? (M ? '아버지' : F ? '어머니' : '부모') : g === 2 ? (M ? '조부' : F ? '조모' : '조부모') : '조상'
  return null
}

// 3계층 노드 칩 — focus 큰 카드 / 앵커 칩(미니 인장) / 일반 소형 칩.
// 탭은 전부 미니 카드 열기(재중심화는 카드 안 동작으로만 — task#197).
function NodeChip({ node, model, onOpenCard, refCb, revealDelay }) {
  const isFocus = node.id === model.focus
  const anchor = hasSymbol(node.slug)
  const tag = roleLabel(node.id, model)
  const reveal = revealDelay !== undefined
    ? { className: 'card-in', animationDelay: `${Math.min(revealDelay, 400)}ms` } : null

  if (isFocus) {
    return (
      <button ref={refCb} onClick={() => onOpenCard(node.id)} style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
        padding: '14px 22px 12px', borderRadius: 14, maxWidth: 'min(320px, 86vw)',
        border: '2px solid var(--gold)', background: 'var(--bg-1)', boxShadow: 'var(--shadow-1)',
        color: 'var(--ink)', font: 'inherit', cursor: 'pointer',
      }}>
        <PersonSymbol slug={node.slug} size={52} style={{ color: 'var(--gold)' }} />
        <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 700 }}>{node.nameKo}</span>
        {node.role && (
          <span style={{ fontSize: 11.5, color: 'var(--ink-faint)', textAlign: 'center', lineHeight: 1.35 }}>
            {node.role}
          </span>
        )}
      </button>
    )
  }

  if (anchor) {
    return (
      <button ref={refCb} onClick={() => onOpenCard(node.id)} title={node.nameKo}
        className={reveal?.className}
        style={{
        ...(reveal ? { animationDelay: reveal.animationDelay } : null),
        display: 'inline-flex', alignItems: 'center', gap: 7, padding: '7px 12px 7px 9px',
        borderRadius: 9, border: '1px solid var(--line-strong)', background: 'var(--bg-1)',
        color: 'var(--ink)', font: 'inherit', fontFamily: 'var(--serif)', fontSize: 13.5,
        fontWeight: 600, cursor: 'pointer', boxShadow: 'var(--shadow-1)', maxWidth: '100%',
      }}>
        <PersonSymbol slug={node.slug} size={22} style={{ color: 'var(--gold)', flexShrink: 0 }} />
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.nameKo}</span>
        {tag && <span style={{ fontSize: 9, fontFamily: 'system-ui', color: 'var(--ink-faint)', fontWeight: 400, flexShrink: 0 }}>{tag}</span>}
      </button>
    )
  }

  return (
    <button ref={refCb} onClick={() => onOpenCard(node.id)} title={node.nameKo}
      className={reveal?.className}
      style={{
      ...(reveal ? { animationDelay: reveal.animationDelay } : null),
      position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '5px 9px', borderRadius: 7, border: '1px solid var(--line)',
      background: 'var(--bg-1)', color: 'var(--ink)', font: 'inherit',
      fontFamily: 'var(--serif)', fontSize: 12.5, fontWeight: 500, cursor: 'pointer', maxWidth: '100%',
    }}>
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.nameKo}</span>
      {tag && <span style={{ fontSize: 9, fontFamily: 'system-ui', color: 'var(--ink-faint)', fontWeight: 400, flexShrink: 0 }}>{tag}</span>}
      {node.authored && <span title="저작 보충" style={{ width: 4, height: 4, borderRadius: '50%', background: TYPE_COLOR.Person, flexShrink: 0 }} />}
    </button>
  )
}

function FamilyTree({ personId, onRecenter = () => {}, onOpenPerson = () => {} }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedSegs, setExpandedSegs] = useState(() => new Set())
  const [expandedGrands, setExpandedGrands] = useState(() => new Set())
  const [cardId, setCardId] = useState(null)
  const [connectors, setConnectors] = useState({ paths: [], w: 0, h: 0 })
  const scrollRef = useRef(null)
  const contentRef = useRef(null)
  const focusCardRef = useRef(null)
  const nodeEls = useRef(new Map())

  useEffect(() => {
    // 부모가 key={familyId}로 리마운트하므로 초기 loading=true가 이미 신선 — effect 동기 setState 불요.
    const ctrl = new AbortController()
    apiGet(`/person/${personId}/family`, { signal: ctrl.signal })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[FamilyTree] 가계도 로드 실패', e); setData(null); setLoading(false) } })
    return () => ctrl.abort()
  }, [personId])

  const model = useMemo(() => (data ? buildModel(data) : null), [data])

  const keyFor = el => cb => { if (cb) nodeEls.current.set(el, cb); else nodeEls.current.delete(el) }

  // 커넥터 — 렌더 후 실측한 칩/세그먼트/그룹 위치로 SVG 경로 계산.
  // 접힌 세그먼트에 삼켜진 조상은 그 세그먼트 칩으로 매핑해 사슬 연속성 유지(중복 경로 디듀프).
  useLayoutEffect(() => {
    const content = contentRef.current
    if (!content || !model) return

    const measure = () => {
      const base = content.getBoundingClientRect()
      const rect = key => {
        const el = nodeEls.current.get(key)
        if (!el) return null
        const r = el.getBoundingClientRect()
        return { x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height }
      }
      // 조상 id → 렌더 키 (직접 노출 or 삼킨 세그먼트)
      const genRowVisible = new Set(model.rows.filter(r => r.type === 'gen').map(r => r.g))
      const segByGen = {}
      for (const r of model.rows) if (r.type === 'segment' && !expandedSegs.has(r.id)) for (const g of r.gens) segByGen[g] = r.id
      const mapKey = id => {
        const g = model.gen[id]
        if (id === model.focus) return 'focus'
        if (g === undefined || g <= 0) return null
        if (genRowVisible.has(g) || expandedSegs.has(segByGen[g] ? segByGen[g] : '')) return `n:${id}`
        if (segByGen[g]) return `seg:${segByGen[g]}`
        return `n:${id}`
      }

      const paths = []
      const seen = new Set()
      const add = (fromKey, toKey, lineage) => {
        if (!fromKey || !toKey || fromKey === toKey) return
        const dk = `${fromKey}>${toKey}`
        if (seen.has(dk)) return
        seen.add(dk)
        const a = rect(fromKey), b = rect(toKey)
        if (!a || !b) return
        const x1 = a.x + a.w / 2, y1 = a.y + a.h
        const x2 = b.x + b.w / 2, y2 = b.y
        if (y2 <= y1) return
        const midY = (y1 + y2) / 2
        paths.push({
          d: `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`,
          lineage: Boolean(lineage),
          // 접힌 세그먼트를 지나는 계보 구간은 금 점선(드로인 대신 — dasharray 충돌)
          dashed: fromKey.startsWith('seg:') || toKey.startsWith('seg:'),
          y1,
        })
      }

      const lin = id => model.byId[id]?.lineage === true
      // ① 조상 사슬(부모→자식, focus 포함)
      for (const [p, c] of model.parentEdges) {
        const gp = model.gen[p], gc = model.gen[c]
        if (gp === undefined || gc === undefined) continue
        if (gp > 0 && (gc > 0 || c === model.focus)) add(mapKey(p), mapKey(c), lin(p) && lin(c))
      }
      // ② focus → 어머니 그룹 (그룹당 1개) — 계보 자식(솔로몬·나단)이 든 그룹만 금실
      model.groups.forEach((grp, gi) =>
        add('focus', `grp:${gi}`, lin(model.focus) && grp.ids.some(lin)))

      // 금실 드로인 순서: 위→아래(y1 오름차순 랭크)
      let rank = 0
      for (const p of [...paths].sort((a, b) => a.y1 - b.y1)) {
        if (p.lineage && !p.dashed) p.delay = Math.min(rank++ * 120, 1200)
      }

      const w = content.scrollWidth, h = content.scrollHeight
      setConnectors(prev => {
        const next = { paths, w, h }
        return JSON.stringify(prev) === JSON.stringify(next) ? prev : next
      })
    }

    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(content)
    return () => ro.disconnect()
  }, [model, expandedSegs, expandedGrands])

  // 에고뷰: 렌더 후 focus 카드가 화면에 오도록 스크롤(조상선이 길어 focus가 하단에 있을 때 필수).
  useLayoutEffect(() => {
    const el = scrollRef.current, card = focusCardRef.current
    if (!el || !card || !model) return
    el.scrollTop = Math.max(0, card.offsetTop - el.clientHeight * 0.35)
  }, [model])

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}><Spinner /></div>
  if (!model || (data && data.nodes.length <= 1)) {
    const name = data?.nodes?.find(n => n.id === personId)?.nameKo
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--ink-faint)', fontSize: 14 }}>
        {name ? `${name}의 ` : ''}혈통 정보가 없습니다.
      </div>
    )
  }

  const { byId, rows, focusRow, groups, grandchildren } = model
  const focusNode = byId[model.focus]
  const rowStyle = {
    display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center',
    gap: 8, maxWidth: '100%',
  }

  // 접힌/펼친 조상 행 렌더 목록 구성(펼친 세그먼트는 그 세대 행들을 인라인 노출)
  const renderedRows = []
  for (const r of rows) {
    if (r.type === 'gen') renderedRows.push(r)
    else if (expandedSegs.has(r.id)) {
      for (const g of r.gens) {
        const ids = Object.keys(model.gen).filter(id => model.gen[id] === g)
          .sort((a, b) => (byId[b].lineage === true) - (byId[a].lineage === true))
        renderedRows.push({ type: 'gen', g, ids, fromSeg: r.id })
      }
    } else renderedRows.push(r)
  }

  return (
    <div className="stage-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg-0)' }}>
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
            onClick={() => onOpenPerson(model.focus)}
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

      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
        <div ref={contentRef} style={{
          position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: 26, padding: '28px 12px 56px', maxWidth: 720, margin: '0 auto',
        }}>
          {/* 커넥터 — 실측 기반. 메시아의 실(lineage)은 금색, 실선 구간은 입장 드로인(위→아래 스태거),
              접힌 세그먼트를 지나는 구간은 금 점선(페이드). reduced-motion은 토큰 가드가 무력화. */}
          <svg width={connectors.w} height={connectors.h}
            style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
            {connectors.paths.map((p, i) => (
              <path key={i} d={p.d} fill="none"
                stroke={p.lineage ? 'var(--gold)' : 'var(--line-strong)'}
                strokeWidth={p.lineage ? 2 : 1.5}
                strokeDasharray={p.dashed ? '5 5' : undefined}
                pathLength={p.lineage && !p.dashed ? 1 : undefined}
                className={p.lineage && !p.dashed ? 'thread-draw' : undefined}
                style={p.delay !== undefined ? { '--thread-delay': `${p.delay}ms` } : undefined}
              />
            ))}
          </svg>

          {/* 조상선 (위 = 오래된 세대) — 펼쳐진 세그먼트의 행은 스태거 페이드(.card-in) */}
          {renderedRows.map((r, ri) => r.type === 'gen' ? (
            <div key={`g${r.g}`} style={rowStyle}>
              {r.ids.map((id, ci) => (
                <NodeChip key={id} node={byId[id]} model={model} onOpenCard={setCardId}
                  refCb={keyFor(`n:${id}`)}
                  revealDelay={r.fromSeg ? ((ri % 8) * 40 + ci * 30) : undefined} />
              ))}
            </div>
          ) : (
            <button key={r.id} ref={keyFor(`seg:${r.id}`)}
              onClick={() => setExpandedSegs(prev => new Set(prev).add(r.id))}
              title="접힌 세대 펼치기"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 14px',
                borderRadius: 999, background: 'var(--bg-0)',
                border: `1px dashed ${r.lineage ? 'var(--gold)' : 'var(--line-strong)'}`,
                color: r.lineage ? 'var(--gold)' : 'var(--ink-faint)',
                font: 'inherit', fontSize: 12, cursor: 'pointer',
              }}>
              ⋯ {r.gens.length}대
            </button>
          ))}

          {/* focus 행: 형제 · focus 카드 · 배우자 (줄바꿈) */}
          <div style={{ ...rowStyle, gap: 10 }}>
            {focusRow.siblings.map(id => (
              <NodeChip key={id} node={byId[id]} model={model} onOpenCard={setCardId} refCb={keyFor(`n:${id}`)} />
            ))}
            <NodeChip node={focusNode} model={model} onOpenCard={setCardId}
              refCb={el => { focusCardRef.current = el; keyFor('focus')(el) }} />
            {focusRow.partners.map(id => (
              <NodeChip key={id} node={byId[id]} model={model} onOpenCard={setCardId} refCb={keyFor(`n:${id}`)} />
            ))}
          </div>

          {/* 자식 세대 — 어머니 그룹 컨테이너 (커넥터는 그룹당 1개) */}
          {groups.length > 0 && (
            <div style={{ ...rowStyle, alignItems: 'flex-start', gap: 12 }}>
              {groups.map((grp, gi) => {
                const grandTotal = grp.ids.reduce((s, cid) => s + (grandchildren[cid]?.length || 0), 0)
                const gKey = `grp-${gi}`
                const mother = grp.motherId ? byId[grp.motherId] : null
                return (
                  <div key={gKey} ref={keyFor(`grp:${gi}`)} style={{
                    display: 'flex', flexDirection: 'column', gap: 8, padding: '9px 11px',
                    borderRadius: 11, border: '1px solid var(--line)', background: 'var(--bg-0)',
                    maxWidth: '100%',
                  }}>
                    {mother && (
                      <span style={{ fontFamily: 'var(--serif)', fontSize: 11, color: 'var(--ink-faint)', textAlign: 'center' }}>
                        {mother.nameKo}
                      </span>
                    )}
                    <div style={{ ...rowStyle, gap: 6 }}>
                      {grp.ids.map(cid => (
                        <NodeChip key={cid} node={byId[cid]} model={model} onOpenCard={setCardId} refCb={keyFor(`n:${cid}`)} />
                      ))}
                    </div>
                    {grandTotal > 0 && !expandedGrands.has(gKey) && (
                      <button onClick={() => setExpandedGrands(prev => new Set(prev).add(gKey))} style={{
                        alignSelf: 'center', padding: '3px 10px', borderRadius: 999,
                        border: '1px dashed var(--line)', background: 'transparent',
                        color: 'var(--ink-faint)', font: 'inherit', fontSize: 11, cursor: 'pointer',
                      }}>
                        손주 {grandTotal}명 · 펼치기
                      </button>
                    )}
                    {expandedGrands.has(gKey) && grp.ids.filter(cid => grandchildren[cid]?.length).map(cid => (
                      <div key={cid} className="card-in" style={{ borderTop: '1px dashed var(--line)', paddingTop: 7, display: 'flex', flexDirection: 'column', gap: 5 }}>
                        <span style={{ fontSize: 10.5, color: 'var(--ink-faint)', textAlign: 'center' }}>
                          {byId[cid].nameKo}의 자녀
                        </span>
                        <div style={{ ...rowStyle, gap: 5 }}>
                          {grandchildren[cid].map((gid, gi2) => (
                            <NodeChip key={gid} node={byId[gid]} model={model} onOpenCard={setCardId}
                              refCb={keyFor(`n:${gid}`)} revealDelay={gi2 * 30} />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* 인물 미니 카드 — 노드 탭으로 열림, 재중심화는 카드 안 동작으로만(task#197) */}
      {cardId && byId[cardId] && (
        <PersonMiniCard
          key={cardId}
          node={byId[cardId]}
          parents={model.parentEdges.filter(([, c]) => c === cardId).map(([p]) => byId[p]).filter(Boolean)}
          isFocus={cardId === model.focus}
          onRecenter={onRecenter}
          onOpenPerson={onOpenPerson}
          onClose={() => setCardId(null)}
        />
      )}
    </div>
  )
}

export default FamilyTree
