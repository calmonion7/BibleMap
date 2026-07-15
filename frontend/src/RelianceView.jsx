import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLangTabs from './VerseLangTabs'

// 하나님 의존 뷰 — 한 인물이 얼마나 하나님을 의지했는가를 도넛 게이지(정의 ii: 물음+순종한 부르심 ÷ 전체)로,
// 하나님-상호작용 순간들을 mode 분해 막대 + 생애 궤적으로, 근거는 양피지 구절 레이어로 보여준다.
// 데이터는 정본 data/god_reliance/<slug>.json을 /person/{id}/reliance API가 서빙(ADR-0023).

// mode 표시 메타 — 순서=의존↔독단 스펙트럼. 색은 듀얼 테마 토큰(양쪽 테마 정의됨).
const MODE_META = {
  '물음-응답': { label: '물음·응답', color: 'var(--valence-pos)', reliance: true },
  '물음-침묵': { label: '물음·침묵', color: 'var(--valence-neutral)', reliance: true },
  '부르심-순종': { label: '부르심·순종', color: 'var(--gold)', reliance: true },
  '부르심-불순종': { label: '부르심·불순종', color: 'var(--type-place)', reliance: false },
  '독단-개입': { label: '독단·은혜개입', color: 'var(--type-event)', reliance: false },
  '독단-어긋남': { label: '독단·어긋남', color: 'var(--valence-neg)', reliance: false },
}
const SEGMENT_ORDER = ['물음-응답', '물음-침묵', '부르심-순종', '부르심-불순종', '독단-개입', '독단-어긋남']

// phase의 mode를 표시 세그먼트 키로 — 부르심은 obeyed로 분리
function segKey(ph) {
  if (ph.mode === '부르심') return ph.obeyed ? '부르심-순종' : '부르심-불순종'
  return ph.mode
}
function segColor(ph) {
  return MODE_META[segKey(ph)]?.color || 'var(--ink-faint)'
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
          style={{ transition: 'stroke-dasharray 0.9s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </g>
      <text x="50%" y="47%" textAnchor="middle" dominantBaseline="middle"
        style={{ fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 34, fill: 'var(--ink)' }}>{percent}%</text>
      <text x="50%" y="65%" textAnchor="middle" dominantBaseline="middle"
        style={{ fontSize: 12, fill: 'var(--ink-faint)' }}>하나님 의존도</text>
    </svg>
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
                    "물음(기도·의탁·예배)"과 "순종한 부르심"이 전체 순간에서 차지하는 비율
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
                <div style={{ overflowX: 'auto', paddingBottom: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'stretch', minWidth: phases.length * 84, position: 'relative' }}>
                    <div style={{ position: 'absolute', top: 30, left: 30, right: 30, height: 2, background: 'var(--line-strong)' }} />
                    {phases.map((ph, i) => (
                      <button key={i} onClick={() => setVerseView({ ph })}
                        style={{
                          flex: 1, minWidth: 84, background: 'none', border: 'none', cursor: 'pointer',
                          padding: '0 4px', display: 'flex', flexDirection: 'column', alignItems: 'center',
                        }}>
                        <span style={{ fontSize: 10, color: 'var(--ink-faint)', marginBottom: 6, height: 14 }}>
                          {ph.approxYear < 0 ? `BC ${-ph.approxYear}` : `AD ${ph.approxYear}`}
                        </span>
                        <span style={{
                          width: 18, height: 18, borderRadius: '50%', background: segColor(ph),
                          border: '2px solid var(--bg-0)', boxShadow: '0 0 0 1px var(--line-strong)', zIndex: 1,
                        }} />
                        <span style={{ fontSize: 10.5, color: 'var(--ink-dim)', marginTop: 8, textAlign: 'center', lineHeight: 1.35, maxWidth: 92 }}>
                          {ph.label.length > 22 ? ph.label.slice(0, 21) + '…' : ph.label}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
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
                        }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--type-event)', whiteSpace: 'nowrap' }}>{ph.verse}</span>
                        <span style={{ fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{ph.label}</span>
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
          style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: segColor(verseView.ph), flexShrink: 0 }} />
              <span style={{ fontWeight: 700, fontSize: 12.5, color: 'var(--paper-accent)' }}>{MODE_META[segKey(verseView.ph)]?.label}</span>
              <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
              <button onClick={() => setVerseView(null)} aria-label="닫기"
                style={{ marginLeft: 'auto', border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--paper-ink)', marginBottom: 10, fontFamily: 'var(--serif)' }}>{verseView.ph.label}</div>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 15.5, lineHeight: 1.8, color: 'var(--paper-ink)' }}>
              <span style={{ fontWeight: 700, color: 'var(--paper-accent)', marginRight: 6 }}>{verseView.ph.verse}</span>
              {verseLang === 'en' && verseView.ph.verseTextEn ? verseView.ph.verseTextEn : (verseView.ph.verseTextKo || verseView.ph.verseTextEn || '구절 본문 없음')}
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* 인물 랭킹 모달 */}
      {(rankLoading || ranking) && createPortal(
        <div onClick={() => { setRanking(null) }}
          style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
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
