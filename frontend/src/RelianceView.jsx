import { useState, useEffect, useRef, useLayoutEffect } from 'react'
import { createPortal } from 'react-dom'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLangTabs from './VerseLangTabs'

// 하나님 의존 뷰 — 한 인물이 얼마나 하나님을 의지했는가를 도넛 게이지(정의 ii: 물음+순종한 부르심 ÷ 전체)로,
// 하나님-상호작용 순간들을 mode 분해 막대 + 생애 궤적으로, 근거는 양피지 구절 레이어로 보여준다.
// 데이터는 정본 data/god_reliance/<slug>.json을 /person/{id}/reliance API가 서빙(ADR-0023).

// mode 표시 메타 — 순서=의존↔독단 스펙트럼. 색은 듀얼 테마 토큰(양쪽 테마 정의됨).
const MODE_META = {
  '물음-응답': { label: '나아감·응답', color: 'var(--valence-pos)', reliance: true },
  '물음-침묵': { label: '나아감·침묵', color: 'var(--valence-neutral)', reliance: true },
  '부르심-순종': { label: '부르심·순종', color: 'var(--gold)', reliance: true },
  '부르심-언약': { label: '부르심·언약', color: 'var(--gold)', reliance: true },
  '부르심-불순종': { label: '부르심·불순종', color: 'var(--type-place)', reliance: false },
  '독단-개입': { label: '독단·은혜개입', color: 'var(--type-event)', reliance: false },
  '독단-어긋남': { label: '독단·어긋남', color: 'var(--valence-neg)', reliance: false },
}
const SEGMENT_ORDER = ['물음-응답', '물음-침묵', '부르심-순종', '부르심-언약', '부르심-불순종', '독단-개입', '독단-어긋남']

// phase의 mode를 표시 세그먼트 키로 — 부르심은 obeyed로 분리
function segKey(ph) {
  if (ph.mode === '부르심') return ph.covenant ? '부르심-언약' : (ph.obeyed ? '부르심-순종' : '부르심-불순종')
  return ph.mode
}
function segColor(ph) {
  return MODE_META[segKey(ph)]?.color || 'var(--ink-faint)'
}

// 구절 레이어 계기→결과 라벨 — segKey별 [계기, 결과]. 부르심은 obeyed로 순종/불순종 파생.
// response(중간 단)가 있는 3단 항목은 STEP_LABELS_3을 쓴다.
const STEP_LABELS_3 = {
  '부르심-순종': ['부르심', '순종', '이루심'],
  '부르심-불순종': ['부르심', '불순종', '심판'],
}
const STEP_LABELS = {
  '물음-응답': ['나아감', '응답'],
  '물음-침묵': ['나아감', '침묵'],
  '부르심-순종': ['부르심', '순종'],
  '부르심-언약': ['부르심', '받음'],
  '부르심-불순종': ['부르심', '불순종'],
  '독단-개입': ['독단', '은혜 개입'],
  '독단-어긋남': ['독단', '어긋남'],
}
// 응답 성격 뱃지 — 물음 계열 outcome.kind → 문구. 부르심/독단은 결과 칩 자체가 성격이라 뱃지 없음.
const KIND_BADGE = {
  '이룸': '그대로 이루심',
  '더하심': '넘치게 이루심',
  '다르게': '다른 방식으로',
  '거절': '그대로는 아니',
  '침묵': '응답하지 않으심',
}

// 계기/결과 라벨 칩 — 모드색 점 + 라벨(양피지 위 가독 위해 텍스트는 paper-ink, 색은 점에만).
function StepChip({ color, text }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span style={{ width: 9, height: 9, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--paper-ink)' }}>{text}</span>
    </span>
  )
}
// 양피지 절 카드 — 모드색 좌측 보더 + 구절 ref + 본문(언어 탭 반영).
function VerseCard({ seg, lang, color }) {
  const txt = lang === 'en' && seg.verseTextEn ? seg.verseTextEn : (seg.verseTextKo || seg.verseTextEn || '구절 본문 없음')
  return (
    <div style={{
      fontFamily: 'var(--serif)', fontSize: 15, lineHeight: 1.8, color: 'var(--paper-ink)',
      borderLeft: `3px solid ${color}`, paddingLeft: 11, marginTop: 6,
    }}>
      <span style={{ fontWeight: 700, color: 'var(--paper-accent)', marginRight: 6 }}>{seg.verse}</span>
      {txt}
    </div>
  )
}

// 도넛 게이지 — 반경 R 원호를 percent만큼 채움. 중앙에 % + '의존도'.
function Donut({ percent }) {
  const R = 58, SW = 12, C = 2 * Math.PI * R, SIZE = (R + SW) * 2
  const filled = (percent / 100) * C
  return (
    <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} style={{ display: 'block' }}>
      <g transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}>
        <circle cx={SIZE / 2} cy={SIZE / 2} r={R} fill="none" stroke="var(--line-strong)" strokeWidth={SW} />
        <circle
          cx={SIZE / 2} cy={SIZE / 2} r={R} fill="none"
          stroke="var(--gold)" strokeWidth={SW} strokeLinecap="round"
          strokeDasharray={`${filled} ${C - filled}`}
          style={{ transition: 'stroke-dasharray 0.9s var(--ease-out)' }}
        />
      </g>
      <text x="50%" y="47%" textAnchor="middle" dominantBaseline="middle"
        style={{ fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 34, fill: 'var(--ink)' }}>{percent}%</text>
      <text x="50%" y="65%" textAnchor="middle" dominantBaseline="middle"
        style={{ fontSize: 12, fill: 'var(--ink-faint)' }}>하나님 의존도</text>
    </svg>
  )
}

// 생애 궤적 — 뱀 배치(boustrophedon): 짝수 행 왼→오, 홀수 행 오→왼. 오른쪽/왼쪽 끝에 닿으면
// 커넥터가 곧게 아래로 내려가 다음 행으로. 가로 스크롤 대신 컨테이너 폭에 맞춰 wrap. 연도순.
const TRAJ_COL_MIN = 92  // 최소 셀 폭(px) — 이보다 좁아지면 행당 개수를 줄인다
const TRAJ_ROW_H = 100   // 행 높이(연도+점+2줄 라벨 + 여백)
const TRAJ_DOT_Y = 24    // 셀 상단→점 중심 오프셋(연도 라벨 높이 + 점 반경)
const TRAJ_CURVE_R = 22  // 코너 곡률 반경 — 턴을 둥근 U자로(딱딱한 직각 대신)

// 점 중심들을 잇는 부드러운 path — 직선 구간은 그대로, 방향이 꺾이는 턴에서만 둥근 코너(2차 베지어).
// 코너 컷은 점(반경 ~11)에 가려져 점을 통과하는 것처럼 보인다.
function roundedPath(pts, r) {
  if (pts.length < 2) return ''
  let d = `M${pts[0].x},${pts[0].y}`
  for (let i = 1; i < pts.length - 1; i++) {
    const p0 = pts[i - 1], p1 = pts[i], p2 = pts[i + 1]
    const d1 = Math.hypot(p1.x - p0.x, p1.y - p0.y) || 1
    const d2 = Math.hypot(p2.x - p1.x, p2.y - p1.y) || 1
    const r1 = Math.min(r, d1 / 2), r2 = Math.min(r, d2 / 2)
    const ax = p1.x + (p0.x - p1.x) / d1 * r1, ay = p1.y + (p0.y - p1.y) / d1 * r1
    const bx = p1.x + (p2.x - p1.x) / d2 * r2, by = p1.y + (p2.y - p1.y) / d2 * r2
    d += ` L${ax},${ay} Q${p1.x},${p1.y} ${bx},${by}`
  }
  const last = pts[pts.length - 1]
  d += ` L${last.x},${last.y}`
  return d
}

function Trajectory({ phases, colorOf, onOpen }) {
  const ref = useRef(null)
  const [w, setW] = useState(0)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const measure = () => setW(el.clientWidth)
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const n = phases.length
  const perRow = w ? Math.max(2, Math.min(n, Math.floor(w / TRAJ_COL_MIN))) : n
  const colW = w ? w / perRow : TRAJ_COL_MIN
  const rowCount = Math.ceil(n / perRow)
  const height = rowCount * TRAJ_ROW_H

  // 뱀 배치 좌표 — 행이 바뀔 때 방향을 뒤집어(짝=정방향, 홀=역방향) 같은 열에서 곧게 내려가게 한다.
  const pos = (gi) => {
    const r = Math.floor(gi / perRow)
    const p = gi % perRow
    const col = r % 2 === 0 ? p : perRow - 1 - p
    return { r, col, cx: col * colW + colW / 2, cy: r * TRAJ_ROW_H + TRAJ_DOT_Y }
  }

  return (
    <div ref={ref} style={{ position: 'relative', height }}>
      {/* 커넥터 — 연속 항목의 점 중심을 잇는다. 같은 행이면 수평선, 행 전환이면 같은 열이라 수직선(곧게 아래로). */}
      {w > 0 && (
        <svg width={w} height={height} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          <path d={roundedPath(phases.map((_, gi) => { const p = pos(gi); return { x: p.cx, y: p.cy } }), TRAJ_CURVE_R)}
            fill="none" stroke="var(--line-strong)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
      {/* 점 + 라벨 — 라벨/연도는 var(--bg-0) 배경으로 뒤의 수직 커넥터를 가린다(끝 열에서만 겹침). */}
      {w > 0 && phases.map((ph, gi) => {
        const { r, col } = pos(gi)
        return (
          <button key={gi} onClick={() => onOpen(ph)}
            style={{
              position: 'absolute', left: col * colW, top: r * TRAJ_ROW_H, width: colW, height: TRAJ_ROW_H,
              padding: '0 4px', border: 'none', background: 'none', cursor: 'pointer',
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              WebkitTapHighlightColor: 'transparent', outline: 'none', userSelect: 'none',
            }}>
            <span style={{ fontSize: 10, color: 'var(--ink-faint)', lineHeight: '13px', height: 13, background: 'var(--bg-0)', padding: '0 3px' }}>
              {ph.approxYear < 0 ? `BC ${-ph.approxYear}` : `AD ${ph.approxYear}`}
            </span>
            <span style={{
              width: 18, height: 18, marginTop: 2, borderRadius: '50%', background: colorOf(ph),
              border: '2px solid var(--bg-0)', boxShadow: '0 0 0 1px var(--line-strong)',
            }} />
            <span style={{
              fontSize: 10.5, color: 'var(--ink-dim)', marginTop: 6, textAlign: 'center', lineHeight: 1.3,
              background: 'var(--bg-0)', padding: '0 2px',
              display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
            }}>
              {ph.trigger?.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function RelianceView({ personId, personName, verseLang, setVerseLang, onSelectPerson }) {
  const [data, setData] = useState(null)
  const [failed, setFailed] = useState(false)
  const [verseView, setVerseView] = useState(null)   // { ph } | null — 궤적 점 클릭 구절 레이어
  const [ranking, setRanking] = useState(null)        // null=미열림, []=로딩, [...]=목록
  const [rankLoading, setRankLoading] = useState(false)

  // 부모가 key={personId}로 리마운트하므로 초기 상태(null/false)가 이미 신선 — effect 내 동기 리셋 불필요.
  useEffect(() => {
    const ctrl = new AbortController()
    apiGet(`/person/${encodeURIComponent(personId)}/reliance`, { signal: ctrl.signal })
      .then(setData)
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[Reliance] 의존도 로드 실패', e); setFailed(true) } })
    return () => ctrl.abort()
  }, [personId])

  function openRanking() {
    if (ranking) return
    setRankLoading(true)
    apiGet('/reliance/ranking')
      .then(({ ranking }) => setRanking(ranking || []))
      .catch(e => { console.warn('[Reliance] 랭킹 로드 실패', e); setRanking([]) })
      .finally(() => setRankLoading(false))
  }

  const name = personName || data?.nameKo || ''

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)', position: 'relative' }}>
      <div style={{ maxWidth: 640, margin: '0 auto', padding: '16px 16px 64px' }}>
        {/* 헤더 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--ink)', fontFamily: 'var(--serif)' }}>
            {name} · 하나님 의존
          </h2>
          <button
            onClick={openRanking}
            style={{
              marginLeft: 'auto', font: 'inherit', fontSize: 12.5, fontWeight: 600, cursor: 'pointer',
              padding: '5px 11px', borderRadius: 8, background: 'var(--bg-2)', color: 'var(--gold)',
              border: '1px solid var(--line-strong)',
            }}
          >인물 랭킹 ↗</button>
        </div>

        {failed && <div style={{ color: 'var(--danger)', fontSize: 13, marginTop: 12 }}>의존도를 불러오지 못했습니다.</div>}
        {!data && !failed && <Spinner />}
        {data && !data.available && (
          <div style={{ fontSize: 13, color: 'var(--ink-faint)', marginTop: 16 }}>
            이 인물의 하나님 의존 데이터가 아직 없습니다.
          </div>
        )}

        {data && data.available && (() => {
          const phases = data.phases || []
          const counts = {}
          for (const ph of phases) { const k = segKey(ph); counts[k] = (counts[k] || 0) + 1 }
          const grace = phases.filter(ph => ph.mode === '독단-개입')
          const total = phases.length || 1
          return (
            <div>
              {/* 도넛 + 백분위 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap', margin: '14px 0 6px' }}>
                <Donut percent={data.percent} />
                <div style={{ minWidth: 180, flex: 1 }}>
                  <div style={{ fontSize: 13.5, color: 'var(--ink-dim)', lineHeight: 1.6 }}>
                    성경 큐레이션 인물 <b style={{ color: 'var(--ink)' }}>{data.total}명</b> 중{' '}
                    <b style={{ color: 'var(--gold)' }}>{data.rank}위</b>
                    <span style={{ color: 'var(--ink-faint)' }}> · 상위 {Math.round((data.rank / data.total) * 100)}%</span>
                  </div>
                  {data.lowSample && (
                    <div style={{
                      display: 'inline-block', marginTop: 8, fontSize: 11.5, fontWeight: 600,
                      color: 'var(--valence-neutral)', background: 'var(--bg-2)',
                      border: '1px solid var(--line-strong)', borderRadius: 6, padding: '3px 8px',
                    }}>표본 적음 (기록 {data.sampleSize}건) — 참고치</div>
                  )}
                  <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginTop: 8, lineHeight: 1.5 }}>
                    "나아감(기도·의탁·예배·헌신)"과 "순종한 부르심"이 전체 순간에서 차지하는 비율
                  </div>
                </div>
              </div>

              {/* mode 분해 막대 */}
              <div style={{ margin: '18px 0 6px' }}>
                <div style={{ display: 'flex', height: 14, borderRadius: 7, overflow: 'hidden', border: '1px solid var(--line)' }}>
                  {SEGMENT_ORDER.filter(k => counts[k]).map(k => (
                    <div key={k} title={`${MODE_META[k].label} ${counts[k]}`}
                      style={{ width: `${(counts[k] / total) * 100}%`, background: MODE_META[k].color }} />
                  ))}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 14px', marginTop: 10 }}>
                  {SEGMENT_ORDER.filter(k => counts[k]).map(k => (
                    <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                      <span style={{ width: 9, height: 9, borderRadius: '50%', background: MODE_META[k].color }} />
                      <span style={{ fontSize: 12, color: 'var(--ink-dim)' }}>{MODE_META[k].label}</span>
                      <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{counts[k]}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* 생애 궤적 — 연도순 mode색 점, 클릭 시 구절 레이어 */}
              <div style={{ marginTop: 22 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)', marginBottom: 4, fontFamily: 'var(--serif)' }}>생애 궤적</div>
                <div style={{ fontSize: 11.5, color: 'var(--ink-faint)', marginBottom: 12 }}>연도순 · 점을 누르면 근거 구절을 봅니다</div>
                <Trajectory phases={phases} colorOf={segColor} onOpen={ph => setVerseView({ ph })} />
              </div>

              {/* 은혜 하이라이트 — 독단이었으나 하나님이 붙드신 순간 */}
              {grace.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--type-event)', marginBottom: 8, fontFamily: 'var(--serif)' }}>
                    은혜의 순간 — 묻지 않았으나 하나님이 붙드심
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {grace.map((ph, i) => (
                      <button key={i} onClick={() => setVerseView({ ph })}
                        style={{
                          textAlign: 'left', cursor: 'pointer', padding: '10px 12px', borderRadius: 10,
                          background: 'var(--bg-1)', border: '1px solid var(--line)', display: 'flex', gap: 10, alignItems: 'baseline',
                          WebkitTapHighlightColor: 'transparent', outline: 'none',
                        }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--type-event)', whiteSpace: 'nowrap' }}>{ph.trigger?.verse}</span>
                        <span style={{ fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{ph.trigger?.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* 방법론 주석 */}
              <div style={{ marginTop: 26, fontSize: 11, color: 'var(--ink-faint)', lineHeight: 1.6, borderTop: '1px solid var(--line)', paddingTop: 12 }}>
                이 수치는 성경에 기록된 주요 결정·기도 순간들에 대한 <b>큐레이션 해석</b>이며 객관적 전수 통계가 아닙니다.
                모든 항목은 구절 근거를 가집니다.
              </div>
            </div>
          )
        })()}
      </div>

      {/* 구절 레이어 — 양피지 포털(WordDistribution·사건 구절 레이어와 동일 패턴) */}
      {verseView && createPortal(
        <div onClick={() => setVerseView(null)}
          className="overlay-in" style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()} className="modal-in"
            style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: segColor(verseView.ph), flexShrink: 0 }} />
              <span style={{ fontWeight: 700, fontSize: 12.5, color: 'var(--paper-accent)' }}>{MODE_META[segKey(verseView.ph)]?.label}</span>
              <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
              <button onClick={() => setVerseView(null)} aria-label="닫기"
                style={{ marginLeft: 'auto', border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
            </div>
            {(() => {
              const ph = verseView.ph
              const [tLabel, rLabel, oLabel] = ph.response
                ? (STEP_LABELS_3[segKey(ph)] || ['계기', '행동', '결과'])
                : (() => { const [t, o] = STEP_LABELS[segKey(ph)] || ['계기', '결과']; return [t, null, o] })()
              const color = segColor(ph)
              const kind = ph.outcome?.kind
              return (
                <div>
                  {/* 계기 */}
                  <StepChip color={color} text={tLabel} />
                  <div style={{ fontSize: 13.5, color: 'var(--paper-ink)', marginTop: 3, fontFamily: 'var(--serif)' }}>{ph.trigger.label}</div>
                  {(ph.response || !ph.sameVerse) && <VerseCard seg={ph.trigger} lang={verseLang} color={color} />}
                  {/* 흐름 화살표 */}
                  <div style={{ textAlign: 'center', color: 'var(--paper-accent)', fontSize: 18, margin: '10px 0', lineHeight: 1 }}>↓</div>
                  {/* 중간 단(행동) — response가 있는 3단 항목만 */}
                  {ph.response && (
                    <>
                      <StepChip color={color} text={rLabel} />
                      <div style={{ fontSize: 13.5, color: 'var(--paper-ink)', marginTop: 3, fontFamily: 'var(--serif)' }}>{ph.response.label}</div>
                      <VerseCard seg={ph.response} lang={verseLang} color={color} />
                      <div style={{ textAlign: 'center', color: 'var(--paper-accent)', fontSize: 18, margin: '10px 0', lineHeight: 1 }}>↓</div>
                    </>
                  )}
                  {/* 결과 */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <StepChip color={color} text={oLabel} />
                    {kind && KIND_BADGE[kind] && (
                      <span style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--paper)', background: 'var(--paper-accent)', borderRadius: 999, padding: '2px 8px' }}>{KIND_BADGE[kind]}</span>
                    )}
                  </div>
                  <div style={{ fontSize: 13.5, color: 'var(--paper-ink)', marginTop: 3, fontFamily: 'var(--serif)' }}>{ph.outcome.label}</div>
                  <VerseCard seg={ph.outcome} lang={verseLang} color={color} />
                </div>
              )
            })()}
          </div>
        </div>,
        document.body
      )}

      {/* 인물 랭킹 모달 */}
      {(rankLoading || ranking) && createPortal(
        <div onClick={() => { setRanking(null) }}
          className="overlay-in" style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()} className="modal-in"
            style={{ background: 'var(--bg-1)', color: 'var(--ink)', borderRadius: 'var(--r-m)', maxWidth: 460, width: '100%', maxHeight: '82%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '16px 18px', border: '1px solid var(--line-strong)' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 700, fontSize: 15, fontFamily: 'var(--serif)', color: 'var(--ink)' }}>하나님 의존도 랭킹</span>
              <button onClick={() => setRanking(null)} aria-label="닫기"
                style={{ marginLeft: 'auto', border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--ink-faint)', lineHeight: 1 }}>×</button>
            </div>
            {rankLoading && <Spinner />}
            {ranking && ranking.map((r, i) => (
              <button key={r.slug}
                onClick={() => { setRanking(null); onSelectPerson && onSelectPerson(r.personId, 'reliance') }}
                style={{
                  width: '100%', textAlign: 'left', cursor: 'pointer', border: 'none', background: r.slug === data?.slug ? 'var(--bg-2)' : 'none',
                  padding: '7px 8px', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 10,
                }}>
                <span style={{ fontSize: 11, color: 'var(--ink-faint)', width: 20, textAlign: 'right' }}>{i + 1}</span>
                <span style={{ fontSize: 13.5, color: 'var(--ink)', width: 88, fontFamily: 'var(--serif)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {r.nameKo}{r.lowSample ? <span style={{ fontSize: 10, color: 'var(--ink-faint)' }}> ·표본적음</span> : ''}
                </span>
                <span style={{ flex: 1, height: 8, background: 'var(--bg-3)', borderRadius: 4, overflow: 'hidden' }}>
                  <span style={{ display: 'block', height: '100%', width: `${r.percent}%`, background: 'var(--gold)' }} />
                </span>
                <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--gold)', width: 38, textAlign: 'right' }}>{r.percent}%</span>
              </button>
            ))}
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default RelianceView
