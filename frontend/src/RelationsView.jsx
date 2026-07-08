import { useState, useEffect } from 'react'
import { Crown, Heart, Handshake, Shield, Scroll, Swords, Users } from 'lucide-react'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'

// 인물 관계 뷰(CONTEXT '인물 관계') — 관계별 줄 개요(인물 헤더 + 사건 시퀀스) + 초점 쌍 + 근거 구절 레이어.
// 전역 시간축 없음(개요) — 각 관계가 자기 줄에 사건을 균등 배치, 시간은 사건 칩의 연도로. person-centric.
const VALENCE_COLOR = { 긍정: '#2e9e5b', 부정: '#d64550', 중립: '#8a94ad' }

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

  const bc = y => `BC ${Math.abs(y)}`
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
        style={{ position: 'absolute', inset: 0, zIndex: 100, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
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
      <div style={{ position: 'relative', height: '100%', overflow: 'hidden', background: '#f7f8fb' }}>
        <div style={{ height: '100%', overflowY: 'auto' }}>
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
        </div>
        {VerseLayer()}
      </div>
    )
  }

  // 개요 — 관계별 한 줄: 인물 헤더(왼쪽) + 사건 시퀀스(오른쪽, 좌→우 · 줄바꿈). 각 관계가 자기 줄을 채움.
  return (
    <div style={{ position: 'relative', height: '100%', overflow: 'hidden', background: '#f7f8fb' }}>
      <div style={{ height: '100%', overflowY: 'auto' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '14px 16px 40px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#2a3350', margin: 0 }}>{personName || '이 인물'}의 관계</h3>
          <span style={{ fontSize: 12, color: '#aab2c5' }}>{relations.length} · 사건 클릭 시 근거 구절</span>
        </div>
        {/* 색 범례 */}
        <div style={{ display: 'flex', gap: 14, marginBottom: 8 }}>
          {Object.entries(VALENCE_COLOR).map(([k, c]) => (
            <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#5a6481' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />{k}
            </span>
          ))}
        </div>
        {/* 관계별 줄 */}
        {sorted.map((r, i) => (
          <div key={i} onClick={() => setFocusIdx(i)} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: '12px 2px', cursor: 'pointer', borderTop: '1px solid #e9ecf2' }}>
            {/* 인물 헤더 (좌, 고정폭) */}
            <div style={{ width: 92, flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, paddingTop: 2 }}>
              <TypeIcon type={r.type} size={20} color={isCurated(r.withId) ? '#4a90d9' : '#8a94ad'} />
              {isCurated(r.withId)
                ? <button onClick={e => { e.stopPropagation(); onExploreJourney(r.withId) }} style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', fontSize: 13, fontWeight: 700, color: '#4a90d9', textAlign: 'center' }}>{r.withNameKo}</button>
                : <span style={{ fontSize: 13, fontWeight: 700, color: '#404a63', textAlign: 'center' }}>{r.withNameKo}</span>}
              <span style={{ fontSize: 10, color: '#aab2c5' }}>{r.type}</span>
            </div>
            {/* 사건 시퀀스 (우, 줄바꿈) */}
            <div style={{ flex: 1, minWidth: 0, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 4, paddingTop: 2 }}>
              {r.phases.map((ph, j) => (
                <span key={j} style={{ display: 'inline-flex', alignItems: 'center' }}>
                  {j > 0 && <span style={{ color: '#c2c8d6', margin: '0 3px', fontSize: 12 }}>→</span>}
                  <button
                    onClick={e => { e.stopPropagation(); setVersePhase({ relIdx: i, phaseIdx: j }) }}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 5, border: '1px solid #e7eaf1', background: '#fff', borderRadius: 999, padding: '4px 10px', cursor: 'pointer' }}
                  >
                    <span style={{ width: 9, height: 9, borderRadius: '50%', flexShrink: 0, background: VALENCE_COLOR[ph.valence] ?? '#8a94ad' }} />
                    <span style={{ fontSize: 12, color: '#2a3350', fontWeight: 500 }}>{ph.label}</span>
                    <span style={{ fontSize: 10, color: '#aab2c5' }}>{bc(ph.approxYear)}</span>
                  </button>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
      </div>
      {VerseLayer()}
    </div>
  )
}

export default RelationsView
