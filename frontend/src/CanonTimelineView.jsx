import { useState, useEffect, useMemo } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { TYPE_COLOR } from './theme'
import { ERA_BANDS } from './eraBands'

// 통사 연표(task#271) — 창세기부터 계시록까지 한 연도 축 위에 시대 밴드·사건 점·인물 활동 막대를 겹친다.
// ERA_BANDS는 TimelineView의 상수를 **재사용**한다(세 번째 복제 금지 — 배포 게이트가 3곳 정합을 검사).
// 데이터는 `/timeline/canon` 하나(신규 저작 0).

const AXIS_W = 3600         // 축 내부 픽셀 폭 — 컨테이너가 가로 스크롤(문서는 스크롤되지 않는다)
const ROW_H = 17            // 인물 막대 한 줄 높이
const DOT = 7               // 사건 점 지름
const DOT_GAP = 2           // 같은 줄에서 두 점 사이 최소 간격
const MAX_LANES = 12        // 사건 점 줄 수 상한
const LANE_H = 12           // 사건 점 줄 간격

export default function CanonTimelineView({ onSelectNode, onSelectPerson, isMobile }) {
  const [data, setData] = useState(null)
  const [failed, setFailed] = useState(false)

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

  // 연도 축 — 데이터의 최소/최대에서 도출. 원시사 밴드의 from은 null(-Infinity)이라 축 왼쪽 끝으로 클램프한다.
  const axis = useMemo(() => {
    if (!data) return null
    const years = [
      ...data.events.map(e => e.year),
      ...data.persons.map(p => p.startYear),
      ...data.persons.map(p => p.endYear),
    ].filter(y => typeof y === 'number' && Number.isFinite(y))
    if (!years.length) return null
    const min = Math.min(...years)
    const max = Math.max(...years)
    const pad = (max - min) * 0.02
    const lo = min - pad
    const hi = max + pad
    return { lo, hi, x: y => ((y - lo) / (hi - lo)) * AXIS_W }
  }, [data])

  // 사건 점 줄 배치 — 연도가 겹치는 사건들이 서로를 덮어 **클릭 불가**가 되지 않게 그리디 패킹.
  // (단순히 index % 3로 흩뿌리면 3칸 떨어진 두 사건이 같은 줄·같은 x에 겹쳐 하나가 포인터를 가로챈다.)
  const laneOf = useMemo(() => {
    if (!data || !axis) return null
    const lastRight = []
    const map = new Map()
    for (const e of [...data.events].sort((a, b) => a.year - b.year)) {
      const left = axis.x(e.year) - DOT / 2
      let lane = lastRight.findIndex(r => r <= left)
      if (lane === -1) {
        if (lastRight.length < MAX_LANES) { lane = lastRight.length; lastRight.push(0) }
        else lane = lastRight.indexOf(Math.min(...lastRight))  // 가장 이른 줄 재사용(겹침 최소화)
      }
      lastRight[lane] = left + DOT + DOT_GAP
      map.set(e.id, lane)
    }
    return map
  }, [data, axis])

  if (failed) return <div style={{ padding: 24, color: 'var(--ink-dim)' }}>통사 연표를 불러오지 못했어요.</div>
  if (!data || !axis) return <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}><Spinner /></div>

  const fmt = y => (y < 0 ? `BC ${Math.round(-y)}` : `AD ${Math.round(y)}`)

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
      <div style={{ padding: isMobile ? '14px 12px 6px' : '18px 24px 8px' }}>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: isMobile ? 19 : 23, fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px' }}>
          통사 연표
        </h1>
        <p style={{ fontSize: 12, color: 'var(--ink-faint)', margin: 0 }}>
          시대 · 사건 {data.events.length}건 · 인물 {data.persons.length}명을 한 연도 축에 — 가로로 밀어 보세요
        </p>
      </div>

      {/* 가로 스크롤은 이 컨테이너 안에서만 — 문서 자체는 가로로 스크롤되지 않는다 */}
      <div data-canon-scroll style={{ overflowX: 'auto', overflowY: 'hidden', padding: isMobile ? '0 12px 32px' : '0 24px 40px' }}>
        <div style={{ width: AXIS_W, position: 'relative' }}>

          {/* 시대 밴드 — 배경 기둥 + 상단 라벨 */}
          <div style={{ position: 'relative', height: 30, marginBottom: 4 }}>
            {ERA_BANDS.map((b, i) => {
              const from = b.from === -Infinity ? axis.lo : b.from
              const to = i + 1 < ERA_BANDS.length ? ERA_BANDS[i + 1].from : axis.hi
              const left = axis.x(from)
              const width = Math.max(2, axis.x(to) - left)
              return (
                <div
                  key={b.name}
                  data-era-band={b.name}
                  style={{
                    position: 'absolute', left, width, top: 0, bottom: 0,
                    borderLeft: '1px solid var(--gold-dim)',
                    background: i % 2 ? 'color-mix(in srgb, var(--gold) 5%, transparent)' : 'transparent',
                    display: 'flex', alignItems: 'center', paddingLeft: 5, boxSizing: 'border-box',
                    overflow: 'hidden',
                  }}
                >
                  <span style={{ fontFamily: 'var(--serif)', fontSize: 11, fontWeight: 700, color: 'var(--gold)', whiteSpace: 'nowrap' }}>
                    {b.name}
                  </span>
                </div>
              )
            })}
          </div>

          {/* 사건 점 — 세 줄로 흩뿌려 밀집 구간에서도 클릭 가능하게 */}
          <div style={{ position: 'relative', height: MAX_LANES * LANE_H + 10, borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)' }}>
            {data.events.map(e => (
              <button
                key={e.id}
                data-canon-event={e.id}
                title={`${e.yearLabel || fmt(e.year)} · ${e.nameKo}${e.bookNameKo ? ` (${e.bookNameKo})` : ''}`}
                onClick={() => onSelectNode?.(e.id)}
                style={{
                  position: 'absolute',
                  left: axis.x(e.year) - DOT / 2,
                  top: 5 + (laneOf?.get(e.id) ?? 0) * LANE_H,
                  width: DOT, height: DOT, padding: 0,
                  borderRadius: '50%', border: 'none', cursor: 'pointer',
                  background: TYPE_COLOR.Event || 'var(--gold)',
                }}
              />
            ))}
          </div>

          {/* 인물 활동 구간 — 시대 순으로 한 줄씩 */}
          <div style={{ position: 'relative', height: data.persons.length * ROW_H + 6, marginTop: 6 }}>
            {data.persons.map((p, i) => {
              const left = axis.x(p.startYear)
              const width = Math.max(6, axis.x(p.endYear) - left)
              return (
                <button
                  key={p.slug}
                  data-canon-person={p.slug}
                  title={`${p.nameKo} · ${fmt(p.startYear)} – ${fmt(p.endYear)} (${p.era})`}
                  onClick={() => onSelectPerson?.(p.id)}
                  style={{
                    position: 'absolute', left, width, top: i * ROW_H,
                    height: ROW_H - 4, padding: 0,
                    borderRadius: 3, border: 'none', cursor: 'pointer',
                    background: `color-mix(in srgb, ${TYPE_COLOR.Person} 55%, transparent)`,
                    display: 'flex', alignItems: 'center', overflow: 'visible',
                  }}
                >
                  <span style={{
                    fontSize: 10, color: 'var(--ink)', whiteSpace: 'nowrap',
                    marginLeft: width < 40 ? width + 4 : 4,
                    fontFamily: 'var(--serif)',
                  }}>{p.nameKo}</span>
                </button>
              )
            })}
          </div>

          {/* 연도 눈금 — 축 양 끝 */}
          <div style={{ position: 'relative', height: 18, marginTop: 4, fontSize: 10, color: 'var(--ink-faint)' }}>
            <span style={{ position: 'absolute', left: 0 }}>{fmt(axis.lo)}</span>
            <span style={{ position: 'absolute', right: 0 }}>{fmt(axis.hi)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
