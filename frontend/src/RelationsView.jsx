import { useState, useEffect } from 'react'
import { Crown, Heart, Handshake, Shield, Scroll, Swords, Users } from 'lucide-react'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'

// 인물 관계 뷰(CONTEXT '인물 관계') — 레인 개요 + 초점 쌍 스토리라인 + 근거 구절 레이어.
// 네트워크 그래프가 아니라 시간축(approxYear) 기반 레이아웃. person-centric.
const VALENCE_COLOR = { 긍정: '#2e9e5b', 부정: '#d64550', 중립: '#8a94ad' }

// 시대 구간 밴드 — 다윗 파일럿 특정(관계 시간축 BC1025~971을 3구간으로 크게 그룹핑). 인물별 일반화는 후속.
const ERA_BANDS = [
  { label: '도피·부상', from: -1025, to: -1003 },
  { label: '통일왕국 확립', from: -1003, to: -990 },
  { label: '왕궁의 위기·계승', from: -990, to: -971 },
]

// 관계 유형(CONTEXT '인물 관계 > 관계 유형') → lucide 아이콘 · 표시 순서(유형끼리 군집 정렬)
const TYPE_ICON = { 가족: Users, 연인: Heart, 친구: Handshake, 신하: Shield, 선지자: Scroll, 군주: Crown, 대적: Swords }
const TYPE_ORDER = ['가족', '연인', '친구', '신하', '선지자', '군주', '대적']
const typeRank = t => { const i = TYPE_ORDER.indexOf(t); return i === -1 ? 99 : i }

function TypeIcon({ type, size = 14, color = '#8a94ad' }) {
  const Icon = TYPE_ICON[type]
  return Icon ? <Icon size={size} color={color} strokeWidth={2} /> : null
}

function RelationsView({ personId, personName, verseLang, setVerseLang, curatedIds = null, onExploreJourney = () => {} }) {
  const [state, setState] = useState({ id: null, relations: null })
  const [focusIdx, setFocusIdx] = useState(null)      // 초점 쌍 인덱스(null = 레인 개요)
  const [versePhase, setVersePhase] = useState(null)  // { relIdx, phaseIdx } | null (구절 레이어)

  useEffect(() => {
    if (!personId) return
    let cancelled = false
    apiGet(`/person/${personId}/relations`)
      .then(d => { if (!cancelled) setState({ id: personId, relations: d.relations ?? [] }) })
      .catch(() => { if (!cancelled) setState({ id: personId, relations: [] }) })
    return () => { cancelled = true }
  }, [personId])

  if (state.id !== personId) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner color="rgba(100,120,180,0.6)" /></div>
  }
  const relations = state.relations || []
  if (relations.length === 0) {
    return <p style={{ padding: 24, color: '#7c8db0', fontSize: 14 }}>이 인물의 관계 데이터가 없습니다.</p>
  }

  // 시간축 — 전 관계 phase의 approxYear 최소~최대.
  const years = relations.flatMap(r => r.phases.map(p => p.approxYear)).filter(y => y != null)
  const minY = Math.min(...years)
  const maxY = Math.max(...years)
  const span = Math.max(1, maxY - minY)
  const pctNum = y => ((y - minY) / span) * 100
  const xPct = y => `${pctNum(y)}%`
  const bc = y => `BC ${Math.abs(y)}`
  // 가장자리 국면 라벨이 이름 칸/우측을 넘지 않도록 앵커 클램프(중앙정렬 대신 좌/우 정렬).
  const labelTransform = y => (pctNum(y) < 12 ? 'translateX(0)' : pctNum(y) > 88 ? 'translateX(-100%)' : 'translateX(-50%)')

  const isCurated = withId => withId && curatedIds?.has(withId)

  // 유형순 정렬(유형끼리 군집, 동일 유형 내 최초 연도). focusIdx·versePhase는 이 sorted 기준.
  const sorted = [...relations].sort((a, b) => {
    const d = typeRank(a.type) - typeRank(b.type)
    if (d !== 0) return d
    return Math.min(...a.phases.map(p => p.approxYear)) - Math.min(...b.phases.map(p => p.approxYear))
  })

  // 근거 구절 레이어
  function VerseLayer() {
    if (!versePhase) return null
    const ph = sorted[versePhase.relIdx]?.phases[versePhase.phaseIdx]
    if (!ph) return null
    const text = verseLang === 'ko' ? ph.verseTextKo : ph.verseTextEn
    return (
      <div
        onClick={() => setVersePhase(null)}
        style={{ position: 'absolute', inset: 0, zIndex: 20, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
      >
        <div onClick={e => e.stopPropagation()} style={{ background: '#fff', borderRadius: 12, maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: '0 8px 32px rgba(0,0,0,0.3)', padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: VALENCE_COLOR[ph.valence] ?? '#8a94ad', flexShrink: 0 }} />
            <span style={{ fontWeight: 700, fontSize: 15, flex: 1 }}>{ph.label}</span>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            <button onClick={() => setVersePhase(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: '#aab2c5', lineHeight: 1, padding: '0 2px' }}>×</button>
          </div>
          <div style={{ fontSize: 12, color: '#8a94ad', marginBottom: 8 }}>{ph.verse} · {bc(ph.approxYear)}</div>
          <p style={{ fontSize: 15, lineHeight: 1.7, color: '#2a3350', margin: 0 }}>{text || '본문을 불러오지 못했습니다.'}</p>
        </div>
      </div>
    )
  }

  // 초점 쌍 — 두 인물 사이 국면 스토리라인
  if (focusIdx != null && sorted[focusIdx]) {
    const r = sorted[focusIdx]
    return (
      <div style={{ position: 'relative', height: '100%', overflowY: 'auto', background: '#f7f8fb' }}>
        <div style={{ maxWidth: 640, margin: '0 auto', padding: '16px 20px 40px' }}>
          <button onClick={() => setFocusIdx(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#5a6481', fontSize: 13, padding: '4px 0', marginBottom: 4 }}>← 관계 전체</button>
          {/* 두 인물 좌우 앵커 + 관계 유형 배지 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '6px 0 20px' }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>{personName || '이 인물'}</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, flexShrink: 0, fontSize: 11, color: '#8a94ad', padding: '2px 8px', borderRadius: 999, background: '#eef0f5' }}>
              <TypeIcon type={r.type} size={13} />{r.type}
            </span>
            <span style={{ flex: 1, height: 1, background: '#d3d8e4' }} />
            {isCurated(r.withId)
              ? <button onClick={() => onExploreJourney(r.withId)} style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', fontWeight: 700, fontSize: 16, color: '#4a90d9' }}>{r.withNameKo} ↗</button>
              : <span style={{ fontWeight: 700, fontSize: 16, color: '#404a63' }}>{r.withNameKo}</span>}
          </div>
          {/* 국면 세로 스토리라인 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {r.phases.map((ph, j) => (
              <div key={j}>
                <button
                  onClick={() => setVersePhase({ relIdx: focusIdx, phaseIdx: j })}
                  style={{ display: 'flex', alignItems: 'flex-start', gap: 12, width: '100%', textAlign: 'left', border: 'none', background: 'none', cursor: 'pointer', padding: '8px 6px', borderRadius: 8 }}
                >
                  <span style={{ width: 14, height: 14, borderRadius: '50%', background: VALENCE_COLOR[ph.valence] ?? '#8a94ad', flexShrink: 0, marginTop: 3 }} />
                  <span style={{ flex: 1 }}>
                    <span style={{ fontWeight: 600, fontSize: 15, color: '#2a3350' }}>{ph.label}</span>
                    <span style={{ display: 'block', fontSize: 12, color: '#8a94ad', marginTop: 2 }}>{bc(ph.approxYear)} · {ph.verse} · 📖 근거 보기</span>
                  </span>
                </button>
                {j < r.phases.length - 1 && <div style={{ width: 2, height: 16, background: '#d3d8e4', marginLeft: 12 }} />}
              </div>
            ))}
          </div>
        </div>
        <VerseLayer />
      </div>
    )
  }

  // 레인 개요 — 관계마다 가로 한 줄, 시간축 위 valence 색 점(교차선 없음) + 시대 밴드 배경 + 국면 라벨
  return (
    <div style={{ position: 'relative', height: '100%', overflowY: 'auto', background: '#f7f8fb' }}>
      <div style={{ maxWidth: 820, margin: '0 auto', padding: '16px 20px 40px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#2a3350', margin: 0 }}>{personName || '이 인물'}의 관계</h3>
          <span style={{ fontSize: 12, color: '#aab2c5' }}>{relations.length} · 레인 클릭 시 상세</span>
        </div>
        {/* 색 범례 (S1) */}
        <div style={{ display: 'flex', gap: 14, marginBottom: 10 }}>
          {Object.entries(VALENCE_COLOR).map(([k, c]) => (
            <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#5a6481' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />{k}
            </span>
          ))}
        </div>
        {/* 시간축 눈금 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#aab2c5', padding: '0 0 0 100px', marginBottom: 4 }}>
          <span>{bc(minY)}</span><span>{bc(maxY)}</span>
        </div>
        {/* 레인 영역 — 시대 밴드(배경) + 레인(전경) */}
        <div style={{ position: 'relative' }}>
          {/* 시대 구간 배경 밴드 (S3) — 트랙 영역(left:100px)에 정렬, 레인 뒤 */}
          <div style={{ position: 'absolute', left: 100, right: 0, top: 0, bottom: 0, zIndex: 0 }}>
            {ERA_BANDS.map((era, i) => (
              <div key={i} style={{
                position: 'absolute', top: 0, bottom: 0,
                left: xPct(era.from), width: `calc(${xPct(era.to)} - ${xPct(era.from)})`,
                background: i % 2 === 0 ? 'rgba(124,156,252,0.07)' : 'rgba(124,156,252,0.13)',
                borderLeft: i === 0 ? 'none' : '1px dashed #cfd6e6',
              }}>
                <span style={{ position: 'absolute', top: 2, left: 5, fontSize: 10, fontWeight: 600, color: '#9aa3ba', whiteSpace: 'nowrap' }}>{era.label}</span>
              </div>
            ))}
          </div>
          {/* 레인(전경) — 시대 라벨용 상단 여백 확보 */}
          <div style={{ position: 'relative', zIndex: 1, paddingTop: 20 }}>
            {sorted.map((r, i) => (
              <div
                key={i}
                onClick={() => setFocusIdx(i)}
                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', cursor: 'pointer', borderTop: '1px solid rgba(226,230,239,0.6)' }}
              >
                {/* 이름 칸 — 관계 유형 아이콘 + 상대 이름(트랙 정렬 위해 width 92 유지) */}
                <div style={{ width: 92, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4, overflow: 'hidden' }}>
                  <TypeIcon type={r.type} size={13} />
                  <span title={r.type} style={{ fontSize: 13, fontWeight: 600, color: isCurated(r.withId) ? '#4a90d9' : '#404a63', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.withNameKo}</span>
                </div>
                <div style={{ position: 'relative', flex: 1, height: 34 }}>
                  <div style={{ position: 'absolute', left: 0, right: 0, top: 8, height: 2, background: '#e2e6ef' }} />
                  {r.phases.map((ph, j) => (
                    <span
                      key={`d${j}`}
                      title={`${ph.label} (${ph.verse})`}
                      style={{
                        position: 'absolute', left: xPct(ph.approxYear), top: 8,
                        transform: 'translate(-50%,-50%)',
                        width: 12, height: 12, borderRadius: '50%',
                        background: VALENCE_COLOR[ph.valence] ?? '#8a94ad',
                        border: '2px solid #fff', boxShadow: '0 0 0 1px rgba(0,0,0,0.08)',
                      }}
                    />
                  ))}
                  {/* 국면 라벨 (S2) — 점 아래, 짝/홀 y 스태거 + 가장자리 앵커 클램프(S4) */}
                  {r.phases.map((ph, j) => (
                    <span
                      key={`l${j}`}
                      style={{
                        position: 'absolute', left: xPct(ph.approxYear), top: j % 2 === 0 ? 15 : 24,
                        transform: labelTransform(ph.approxYear), fontSize: 9, lineHeight: 1,
                        color: '#6a7492', whiteSpace: 'nowrap', pointerEvents: 'none',
                      }}
                    >{ph.label}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <VerseLayer />
    </div>
  )
}

export default RelationsView
