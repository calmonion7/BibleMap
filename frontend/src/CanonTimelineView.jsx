import { useState, useEffect, useMemo, useRef } from 'react'
import { ChevronDown } from 'lucide-react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { TYPE_COLOR } from './theme'
import { ERA_BANDS } from './eraBands'

// 통사 연표(task#271→272) — 창세기부터 계시록까지 8개 시대를 세로 섹션으로 쌓는다.
// 1차 좌표는 시대 순서, 연도 비례는 시대 안에서만(ADR 260819-210927 — 가로 선형 축은
// 신약 33%가 9.5px로 무너져 폐기). ERA_BANDS는 TimelineView와 공유(재선언 금지).
// 데이터는 `/timeline/canon` 하나(신규 저작 0).

// sticky 시대 칩 스트립이 섹션 상단을 가려 스크롤 타깃(토글/행)의 클릭을 가로채는 걸 막는
// 여유값 — Playwright의 "intercepts pointer events"는 테스트 문제가 아니라 UX 결함(회고 260819-205246).
const STRIP_SAFE = { mobile: 120, desktop: 78 }

const fmt = y => (y < 0 ? `BC ${Math.round(-y)}` : `AD ${Math.round(y)}`)

export default function CanonTimelineView({ onSelectNode, onSelectPerson, isMobile }) {
  const [data, setData] = useState(null)
  const [failed, setFailed] = useState(false)
  const [expanded, setExpanded] = useState(() => new Set())
  const [activeEra, setActiveEra] = useState(ERA_BANDS[0].name)
  const rootRef = useRef(null)
  const stripRef = useRef(null)
  const sectionRefs = useRef({})

  useEffect(() => {
    const ctrl = new AbortController()
    let alive = true
    apiGet('/timeline/canon', { signal: ctrl.signal })
      .then(d => { if (alive) setData(d) })
      .catch(e => {
        if (e?.name !== 'AbortError') { console.warn('[CanonTimeline] 통사 연표 로드 실패', e); if (alive) setFailed(true) }
      })
    return () => { alive = false; ctrl.abort() }
  }, [])

  // 시대별 사건·인물 묶음 — event.era/person.era 값은 ERA_BANDS 이름과 정확히 일치한다는 계약(API 스펙).
  const byEra = useMemo(() => {
    if (!data) return null
    const map = new Map(ERA_BANDS.map(b => [b.name, { events: [], persons: [] }]))
    for (const e of data.events) map.get(e.era)?.events.push(e)
    for (const p of data.persons) map.get(p.era)?.persons.push(p)
    for (const g of map.values()) g.events.sort((a, b) => a.year - b.year)
    return map
  }, [data])

  // 시대 내 연도 비례 축 — 경계는 ERA_BANDS[i].from ~ ERA_BANDS[i+1].from.
  // 원시사(from=-Infinity)와 신약(다음 밴드 없음)의 열린 끝은 데이터 실측 최소/최대로 클램프.
  const eraRanges = useMemo(() => {
    if (!data) return null
    const years = [
      ...data.events.map(e => e.year),
      ...data.persons.map(p => p.startYear),
      ...data.persons.map(p => p.endYear),
    ]
    const min = Math.min(...years)
    const max = Math.max(...years)
    return ERA_BANDS.map((b, i) => ({
      from: b.from === -Infinity ? min : b.from,
      to: i + 1 < ERA_BANDS.length ? ERA_BANDS[i + 1].from : max,
    }))
  }, [data])

  const pct = (y, range) => {
    const span = range.to - range.from
    return span > 0 ? Math.min(100, Math.max(0, ((y - range.from) / span) * 100)) : 50
  }

  const toggleEra = (name) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(name) ? next.delete(name) : next.add(name)
      return next
    })
  }

  // 칩 탭 → 해당 섹션 상단으로 스크롤(sticky 스트립 높이만큼 보정) + 활성 칩 즉시 갱신.
  const scrollToEra = (name) => {
    const root = rootRef.current
    const el = sectionRefs.current[name]
    if (!root || !el) return
    const rootRect = root.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    const stripH = stripRef.current ? stripRef.current.getBoundingClientRect().height : 0
    root.scrollBy({ top: elRect.top - rootRect.top - stripH - 4, behavior: 'smooth' })
    setActiveEra(name)
  }

  // 스크롤 위치로 현재 시대 판정(스크롤스파이) — 시대가 8개뿐이라 매 스크롤에 다시 재도 가볍다.
  const handleScroll = () => {
    const root = rootRef.current
    if (!root) return
    const threshold = root.getBoundingClientRect().top + (stripRef.current?.getBoundingClientRect().height || 0) + 4
    let current = ERA_BANDS[0].name
    for (const b of ERA_BANDS) {
      const el = sectionRefs.current[b.name]
      if (el && el.getBoundingClientRect().top <= threshold) current = b.name
    }
    setActiveEra(current)
  }

  if (failed) return <div style={{ padding: 24, color: 'var(--ink-dim)' }}>통사 연표를 불러오지 못했어요.</div>
  if (!data || !byEra || !eraRanges) return <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}><Spinner /></div>

  const stripSafe = isMobile ? STRIP_SAFE.mobile : STRIP_SAFE.desktop

  return (
    <div
      data-canon-view
      ref={rootRef}
      onScroll={handleScroll}
      style={{ height: '100%', overflowY: 'auto', overflowX: 'hidden', background: 'var(--bg-0)', WebkitTapHighlightColor: 'transparent' }}
    >
      <div style={{ padding: isMobile ? '14px 12px 4px' : '18px 24px 6px' }}>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: isMobile ? 19 : 23, fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px' }}>
          통사 연표
        </h1>
        <p style={{ fontSize: 12, color: 'var(--ink-faint)', margin: 0 }}>
          시대 8개 · 사건 {data.events.length}건 · 인물 {data.persons.length}명 — 시대를 눌러 사건을 펼쳐보세요
        </p>
      </div>

      {/* 시대 점프 칩 스트립 — sticky, 2줄 래핑으로 390px에 수용(가로 스크롤 금지) */}
      <div
        data-era-strip
        ref={stripRef}
        style={{
          position: 'sticky', top: 0, zIndex: 2,
          background: 'var(--bg-0)', borderBottom: '1px solid var(--line)',
          padding: isMobile ? '8px 12px' : '10px 24px',
          display: 'grid', gridTemplateColumns: `repeat(${isMobile ? 4 : 8}, 1fr)`, gap: 6,
        }}
      >
        {ERA_BANDS.map(b => {
          const active = activeEra === b.name
          return (
            <button
              key={b.name}
              data-era-chip={b.name}
              data-era-chip-active={active ? 'true' : undefined}
              onClick={() => scrollToEra(b.name)}
              style={{
                minHeight: 44, minWidth: 40, boxSizing: 'border-box',
                border: `1px solid ${active ? 'var(--gold)' : 'var(--line)'}`, borderRadius: 'var(--r-s)',
                cursor: 'pointer', font: 'inherit', fontSize: 11, lineHeight: 1.25, padding: '4px 3px',
                background: active ? 'var(--gold)' : 'var(--bg-1)', color: active ? 'var(--bg-0)' : 'var(--ink-dim)',
                fontWeight: active ? 700 : 500,
              }}
            >
              {b.name}
            </button>
          )
        })}
      </div>

      {ERA_BANDS.map((b, i) => {
        const group = byEra.get(b.name)
        const range = eraRanges[i]
        const isExpanded = expanded.has(b.name)
        return (
          <section
            key={b.name}
            data-era-section={b.name}
            ref={el => { sectionRefs.current[b.name] = el }}
            style={{ scrollMarginTop: stripSafe, padding: isMobile ? '10px 12px 16px' : '14px 24px 20px', borderBottom: '1px solid var(--line)' }}
          >
            {/* 시대 헤더 — 탭하면 사건 목록 펼침/접힘(기본 접힘, 신약 236건이 첫 화면을 삼키지 않게) */}
            <button
              data-era-toggle
              onClick={() => toggleEra(b.name)}
              aria-expanded={isExpanded}
              style={{
                width: '100%', minHeight: 44, boxSizing: 'border-box', scrollMarginTop: stripSafe,
                display: 'flex', alignItems: 'center', gap: 8, textAlign: 'left',
                background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', padding: '6px 0',
              }}
            >
              <span style={{ fontFamily: 'var(--serif)', fontSize: isMobile ? 15 : 17, fontWeight: 700, color: 'var(--gold)' }}>{b.name}</span>
              <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{b.range}</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: 11.5, color: 'var(--ink-dim)' }}>사건 {group.events.length} · 인물 {group.persons.length}</span>
              <ChevronDown
                size={16} color="var(--ink-faint)"
                style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform var(--dur-fast) var(--ease-out)', flexShrink: 0 }}
              />
            </button>

            {/* 인물 활동 레인 — 시대 내 연도 비례 막대, 라벨은 항상 노출(시대당 2~6명) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
              {group.persons.map(p => {
                const left = pct(Math.min(p.startYear, p.endYear), range)
                const right = pct(Math.max(p.startYear, p.endYear), range)
                const width = Math.max(2, right - left)
                return (
                  <button
                    key={p.slug}
                    data-canon-person={p.slug}
                    onClick={() => onSelectPerson?.(p.id)}
                    title={`${p.nameKo} · ${fmt(p.startYear)} – ${fmt(p.endYear)}`}
                    style={{
                      position: 'relative', minHeight: 44, width: '100%', boxSizing: 'border-box',
                      border: 'none', borderRadius: 'var(--r-s)', cursor: 'pointer', textAlign: 'left',
                      background: 'var(--bg-1)', padding: '4px 10px', display: 'flex', alignItems: 'center', overflow: 'hidden',
                    }}
                  >
                    <span
                      style={{
                        position: 'absolute', left: `${left}%`, width: `${width}%`, top: 4, bottom: 4,
                        borderRadius: 3, background: `color-mix(in srgb, ${TYPE_COLOR.Person} 45%, transparent)`,
                      }}
                    />
                    <span style={{ position: 'relative', fontFamily: 'var(--serif)', fontSize: 13, color: 'var(--ink)', zIndex: 1 }}>{p.nameKo}</span>
                  </button>
                )
              })}
            </div>

            {/* 사건 밀도 띠 — 비대화형(div, button 아님) + pointerEvents:none. 겹침은 결함이 아니라 밀도 정보(ADR 260819-210927). */}
            <div style={{ fontSize: 10, color: 'var(--ink-faint)', marginTop: 10 }}>사건 분포 · {group.events.length}건</div>
            <div style={{ position: 'relative', height: 16, marginTop: 3, pointerEvents: 'none' }} aria-hidden="true">
              {group.events.map(e => (
                <div
                  key={e.id}
                  style={{
                    position: 'absolute', left: `calc(${pct(e.year, range)}% - 1.5px)`, top: 0,
                    width: 3, height: '100%', borderRadius: 1, background: TYPE_COLOR.Event,
                  }}
                />
              ))}
            </div>

            {/* 사건 목록 — 펼쳤을 때만 렌더(713건 전부를 접힌 상태에서도 DOM에 둘 필요 없음) */}
            {isExpanded && (
              <div style={{ display: 'flex', flexDirection: 'column', marginTop: 8 }}>
                {group.events.map(e => (
                  <button
                    key={e.id}
                    data-canon-event-row={e.id}
                    onClick={() => onSelectNode?.(e.id)}
                    style={{
                      minHeight: 44, width: '100%', boxSizing: 'border-box', scrollMarginTop: stripSafe,
                      display: 'flex', alignItems: 'center', gap: 8, textAlign: 'left',
                      border: 'none', borderBottom: '1px solid var(--line)', background: 'none', cursor: 'pointer', font: 'inherit',
                      padding: '8px 4px',
                    }}
                  >
                    <span style={{ fontSize: 11, color: 'var(--ink-faint)', flexShrink: 0, minWidth: isMobile ? 62 : 76 }}>{e.yearLabel || fmt(e.year)}</span>
                    <span style={{ fontSize: 13, color: 'var(--ink)', flex: 1, minWidth: 0 }}>{e.nameKo}</span>
                    {e.bookNameKo && <span style={{ fontSize: 11, color: 'var(--ink-faint)', flexShrink: 0 }}>{e.bookNameKo}</span>}
                  </button>
                ))}
              </div>
            )}
          </section>
        )
      })}
    </div>
  )
}
