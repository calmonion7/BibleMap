import { useState, useEffect } from 'react'
import { Crown, Heart, Handshake, Shield, Scroll, Swords, Users, GraduationCap, Sun, Network, HeartHandshake } from 'lucide-react'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'
import PersonSymbol, { hasSymbol } from './personSymbols'
import { VALENCE_COLOR } from './theme'

// 인물 관계 뷰(CONTEXT '인물 관계') — 유형 섹션 + 관계 카드(인장 아바타 + 사건 칩) 개요 + 초점 쌍 + 근거 구절 레이어.
// 전역 시간축 없음(개요) — 칩은 시간순 나열, 시간은 칩의 연도로. person-centric. (task#198 카드형 개편)
// 모션은 :active 피드백만 — 레인 입장 모션은 모션 오디트 기각 유지(밀도 데이터 장식 방해·고빈도 탭).

// 관계 유형(CONTEXT '인물 관계 > 관계 유형') → lucide 아이콘 · 표시 순서(유형끼리 군집 정렬)
const TYPE_ICON = { 가족: Users, 연인: Heart, 친구: Handshake, 신하: Shield, 선지자: Scroll, 스승제자: GraduationCap, 군주: Crown, 하나님: Sun, 대적: Swords }
const TYPE_ORDER = ['하나님', '가족', '연인', '친구', '신하', '선지자', '스승제자', '군주', '대적']
const typeRank = t => { const i = TYPE_ORDER.indexOf(t); return i === -1 ? 99 : i }

function TypeIcon({ type, size = 14, color = 'var(--ink-faint)' }) {
  const Icon = TYPE_ICON[type]
  return Icon ? <Icon size={size} color={color} strokeWidth={2} /> : null
}

// 상대 인물 아바타 — 큐레이션 상대(인장 보유)는 선화 인장, 아니면 유형 아이콘 폴백(ADR-0025 4번째 사용처)
function PartnerAvatar({ slug, type, size = 38, curated }) {
  const frame = {
    width: size + 14, height: size + 14, borderRadius: '50%', flexShrink: 0,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    border: `1px solid ${curated ? 'var(--gold-dim)' : 'var(--line-strong)'}`,
    color: curated ? 'var(--gold)' : 'var(--ink-faint)', background: 'var(--bg-1)',
  }
  return (
    <span style={frame}>
      {hasSymbol(slug)
        ? <PersonSymbol slug={slug} size={size} />
        : <TypeIcon type={type} size={Math.round(size * 0.55)} color="currentColor" />}
    </span>
  )
}

function RelationsView({ personId, personName, verseLang, setVerseLang, curatedIds = null, onExploreJourney = () => {}, onSwitchView = null, onOpenFamily = null }) {
  const [state, setState] = useState({ id: null, relations: null })
  const [focusIdx, setFocusIdx] = useState(null)      // 초점 쌍 인덱스(null = 카드 개요)
  const [versePhase, setVersePhase] = useState(null)  // { relIdx, phaseIdx } | null (구절 레이어)

  useEffect(() => {
    if (!personId) return
    let cancelled = false
    apiGet(`/person/${personId}/relations`)
      .then(d => { if (!cancelled) setState({ id: personId, relations: d.relations ?? [] }) })
      .catch(e => { if (!cancelled) { console.warn('[Relations] 관계 로드 실패', e); setState({ id: personId, relations: [] }) } })
    return () => { cancelled = true }
  }, [personId])

  if (state.id !== personId) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner color="var(--gold)" /></div>
  }
  const relations = state.relations || []
  if (relations.length === 0) {
    return <p style={{ padding: 24, color: 'var(--ink-faint)', fontSize: 14 }}>이 인물의 관계 데이터가 없습니다.</p>
  }

  const era = y => y < 0 ? `BC ${-y}` : `AD ${y}`
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
    const ctx = verseLang === 'ko' ? ph.contextKo : ph.contextEn
    const text = verseLang === 'ko' ? ph.verseTextKo : ph.verseTextEn
    return (
      <div
        onClick={() => setVersePhase(null)}
        // 모달 스크림 — 전용 토큰 없어 값 유지(다크 배경 위 반투명 오버레이라 무해)
        style={{ position: 'absolute', inset: 0, zIndex: 100, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
      >
        {/* 근거 구절 모달 = 양피지 카드(원칙 2) */}
        <div onClick={e => e.stopPropagation()} style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: VALENCE_COLOR[ph.valence] ?? VALENCE_COLOR.중립, flexShrink: 0 }} />
            <span style={{ fontWeight: 700, fontSize: 15, flex: 1 }}>{ph.label}</span>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            <button onClick={() => setVersePhase(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
          </div>
          <div style={{ fontSize: 12, color: 'var(--paper-accent)', marginBottom: 8 }}>{ph.verse} · {era(ph.approxYear)}</div>
          {Array.isArray(ctx) && ctx.length ? (
            <p style={{ fontSize: 15, lineHeight: 1.8, fontFamily: 'var(--serif)', color: 'var(--paper-ink)', margin: 0 }}>
              {ctx.map((c, i) => (
                <span key={i} style={c.a ? { fontWeight: 700, color: 'var(--paper-accent)' } : undefined}>
                  <sup style={{ color: 'var(--paper-accent)', fontWeight: 400, marginRight: 1 }}>{c.v}</sup>{c.t}{i < ctx.length - 1 ? ' ' : ''}
                </span>
              ))}
            </p>
          ) : (
            <p style={{ fontSize: 15, lineHeight: 1.8, fontFamily: 'var(--serif)', color: 'var(--paper-ink)', margin: 0 }}>{text || '본문을 불러오지 못했습니다.'}</p>
          )}
        </div>
      </div>
    )
  }

  // 초점 쌍 — 두 인물 사이 국면 스토리라인
  if (focusIdx != null && sorted[focusIdx]) {
    const r = sorted[focusIdx]
    return (
      <div style={{ position: 'relative', height: '100%', overflow: 'hidden', background: 'var(--bg-0)', WebkitTapHighlightColor: 'transparent' }}>
        <div style={{ height: '100%', overflowY: 'auto' }}>
        {/* 초점 쌍 콘텐츠 폭 제한 — 감사 M5(여백 과다) 해소 */}
        <div style={{ maxWidth: 880, margin: '0 auto', padding: '16px 20px 40px' }}>
          <button onClick={() => setFocusIdx(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'var(--ink-dim)', fontSize: 13, padding: '4px 0', marginBottom: 4 }}>← 관계 전체</button>
          {/* 두 인물 마주보기 앵커 — 상대는 인장 아바타(비큐레이션 유형 아이콘 폴백), 가운데 유형 배지 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '10px 0 24px' }}>
            <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, minWidth: 72 }}>
              <span style={{ fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 16, color: 'var(--ink)' }}>{personName || '이 인물'}</span>
            </span>
            <span style={{ flex: 1, height: 1, background: 'var(--line-strong)' }} />
            <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 2, flexShrink: 0 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--ink-faint)', padding: '2px 8px', borderRadius: 999, background: 'var(--bg-2)' }}>
                <TypeIcon type={r.type} size={13} />{r.type}
              </span>
              {r.note && <span style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{r.note}</span>}
            </span>
            <span style={{ flex: 1, height: 1, background: 'var(--line-strong)' }} />
            <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, minWidth: 72 }}>
              <PartnerAvatar slug={r.withSlug} type={r.type} size={40} curated={isCurated(r.withId)} />
              {isCurated(r.withId)
                ? <button onClick={() => onExploreJourney(r.withId)} style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 16, color: 'var(--gold)' }}>{r.withNameKo} ↗</button>
                : <span style={{ fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 16, color: 'var(--ink)' }}>{r.withNameKo}</span>}
            </span>
          </div>
          {/* 국면 세로 스토리라인 — 연속 레일 위 valence 점 */}
          <div style={{ position: 'relative', paddingLeft: 2 }}>
            {r.phases.length > 1 && <span style={{ position: 'absolute', left: 12, top: 14, bottom: 14, width: 2, background: 'var(--line-strong)' }} />}
            {r.phases.map((ph, j) => (
              <button
                key={j}
                onClick={() => setVersePhase({ relIdx: focusIdx, phaseIdx: j })}
                className="pressable"
                style={{ position: 'relative', display: 'flex', alignItems: 'flex-start', gap: 12, width: '100%', textAlign: 'left', border: 'none', background: 'none', cursor: 'pointer', padding: '10px 6px 10px 4px', borderRadius: 8 }}
              >
                <span style={{ width: 14, height: 14, borderRadius: '50%', background: VALENCE_COLOR[ph.valence] ?? VALENCE_COLOR.중립, flexShrink: 0, marginTop: 3, boxShadow: '0 0 0 3px var(--bg-0)' }} />
                <span style={{ flex: 1 }}>
                  <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--ink)' }}>{ph.label}</span>
                  <span style={{ display: 'block', fontSize: 12, color: 'var(--ink-faint)', marginTop: 2 }}>{era(ph.approxYear)} · {ph.verse} · 📖 근거 보기</span>
                </span>
              </button>
            ))}
          </div>
        </div>
        </div>
        {VerseLayer()}
      </div>
    )
  }

  // 개요 — 유형 섹션 헤더 + 관계 카드(상단 신원 행 + 전폭 사건 칩). 좁은 좌측 열 구조를 카드형으로 교체(task#198).
  return (
    <div style={{ position: 'relative', height: '100%', overflow: 'hidden', background: 'var(--bg-0)', WebkitTapHighlightColor: 'transparent' }}>
      <div style={{ height: '100%', overflowY: 'auto' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '14px 16px 40px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
          <h3 style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, color: 'var(--ink)', margin: 0 }}>{personName || '이 인물'}의 관계</h3>
          <span style={{ fontSize: 12, color: 'var(--ink-faint)' }}>{relations.length} · 사건 클릭 시 근거 구절</span>
          {/* 색 범례 — 헤더 우측 정렬(모바일은 자연 줄바꿈) */}
          <span style={{ marginLeft: 'auto', display: 'inline-flex', gap: 12 }}>
            {Object.entries(VALENCE_COLOR).map(([k, c]) => (
              <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--ink-dim)' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />{k}
              </span>
            ))}
          </span>
        </div>
        {/* 유형 섹션 + 관계 카드 */}
        {sorted.map((r, i) => {
          const newSection = i === 0 || sorted[i - 1].type !== r.type
          const count = newSection ? sorted.filter(x => x.type === r.type).length : 0
          return (
            <div key={i}>
              {newSection && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '18px 0 8px' }}>
                  <TypeIcon type={r.type} size={15} color="var(--gold-dim)" />
                  <span style={{ fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, color: 'var(--ink-dim)', letterSpacing: '0.06em' }}>{r.type}</span>
                  {count > 1 && <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{count}</span>}
                  <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
                </div>
              )}
              <div
                onClick={() => setFocusIdx(i)}
                className="pressable"
                style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '12px 14px', marginBottom: 8, cursor: 'pointer', border: '1px solid var(--line)', borderRadius: 'var(--r-m)', background: 'var(--bg-1)' }}
              >
                {/* 신원 행 — 인장 아바타 + 이름 + 역할 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <PartnerAvatar slug={r.withSlug} type={r.type} curated={isCurated(r.withId)} />
                  <span style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
                    {isCurated(r.withId)
                      ? <button onClick={e => { e.stopPropagation(); onExploreJourney(r.withId) }} style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, color: 'var(--gold)', textAlign: 'left' }}>{r.withNameKo} ↗</button>
                      : <span style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, color: 'var(--ink)' }}>{r.withNameKo}</span>}
                    {r.note && <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{r.note}</span>}
                  </span>
                  <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--ink-faint)', flexShrink: 0 }}>국면 {r.phases.length}</span>
                </div>
                {/* 사건 칩 — 시간순(읽기 순서 = 시간, 화살표 제거로 줄바꿈 혼선 해소) */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {r.phases.map((ph, j) => (
                    <button
                      key={j}
                      className="rel-chip"
                      onClick={e => { e.stopPropagation(); setVersePhase({ relIdx: i, phaseIdx: j }) }}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 5, borderRadius: 999, padding: '4px 10px', cursor: 'pointer' }}
                    >
                      <span style={{ width: 9, height: 9, borderRadius: '50%', flexShrink: 0, background: VALENCE_COLOR[ph.valence] ?? VALENCE_COLOR.중립 }} />
                      <span style={{ fontSize: 12, color: 'var(--ink)', fontWeight: 500 }}>{ph.label}</span>
                      <span style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{era(ph.approxYear)}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
        {/* 다른 축 안내 푸터 — 저밀도 인물의 하단 공백을 탐색 동선으로 마무리(S3) */}
        {(onOpenFamily || onSwitchView) && (
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--line)' }}>
            <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginBottom: 10 }}>다른 축으로 살펴보기</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {onOpenFamily && (
                <button onClick={() => onOpenFamily()} className="pressable" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 14px', borderRadius: 999, border: '1px solid var(--line-strong)', background: 'var(--bg-1)', color: 'var(--ink-dim)', fontSize: 13, cursor: 'pointer' }}>
                  <Network size={14} />족보 — 혈통으로 보기
                </button>
              )}
              {onSwitchView && (
                <button onClick={() => onSwitchView('reliance')} className="pressable" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 14px', borderRadius: 999, border: '1px solid var(--line-strong)', background: 'var(--bg-1)', color: 'var(--ink-dim)', fontSize: 13, cursor: 'pointer' }}>
                  <HeartHandshake size={14} />의존 — 하나님과의 관계
                </button>
              )}
            </div>
          </div>
        )}
      </div>
      </div>
      {VerseLayer()}
    </div>
  )
}

export default RelationsView
