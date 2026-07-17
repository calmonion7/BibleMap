import { useState, useEffect } from 'react'
import { Route, Clock, Users } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import { apiGet } from './api'
import VerseLayer, { paperTextStyle } from './VerseLayer'
import Spinner from './Spinner'
import PersonSymbol from './personSymbols'

// 인물 소개(intro) 전용 뷰 — 상세 시트(SidePanel) 재사용에서 분리한 전용 페이지(explore intro 탭).
// 구성: 정체성 헤더 → 소개문(근거 구절 칩) → 인물 성품 → 관문 요약(여정/타임라인/관계 점프).
// role/intro/verses는 Part 1이 노드에 주입한 속성. era/eventCount는 /persons/curated에만 존재.
// 함께등장·동시대·그래프이웃 인물 리스트는 여기서 부재 — 관계는 관계 탭 전담(원칙: 소개는 정체성).

// 생몰 라벨 — birthYear/deathYear("-4004" 형식 음수=BC). parseYear는 문자열만 반환해 범위·나이 계산엔
// 부적합하므로 정수 파싱 후 직접 조립. 둘 다 없으면 null(생몰 미표시).
function formatLifespan(birthYear, deathYear) {
  const b = birthYear != null ? parseInt(birthYear, 10) : null
  const d = deathYear != null ? parseInt(deathYear, 10) : null
  if (b == null || Number.isNaN(b)) {
    if (d == null || Number.isNaN(d)) return null
  }
  const era = y => (y < 0 ? 'BC' : 'AD')
  const abs = y => Math.abs(y)
  const hasB = b != null && !Number.isNaN(b)
  const hasD = d != null && !Number.isNaN(d)
  let range
  if (hasB && hasD) {
    range = era(b) === era(d)
      ? `${era(b)} ${abs(b)}–${abs(d)}`
      : `${era(b)} ${abs(b)} – ${era(d)} ${abs(d)}`
  } else {
    const y = hasB ? b : d
    range = `${era(y)} ${abs(y)}`
  }
  const age = hasB && hasD ? Math.abs(d - b) : null
  return age != null ? `${range} · ${age}세` : range
}

// 근거 구절 칩 — 다른 곳(SidePanel)의 placeChipBase 톤 답습. 클릭 시 양피지 레이어.
const chipStyle = {
  display: 'inline-flex', alignItems: 'center', gap: 3,
  fontSize: 11, padding: '2px 8px', borderRadius: 999, lineHeight: 1.7,
  border: '1px solid var(--line-strong)', cursor: 'pointer', fontWeight: 600,
  background: 'var(--bg-2)', color: TYPE_COLOR.Book,
}

function PersonIntro({ personId, verseLang, setVerseLang, onSwitchView = () => {}, onOpenFamily = () => {}, journeyStops = null, personEventIds = null }) {
  // 노드/메타 fetch — 어느 personId의 결과인지 id로 추적(stale 응답 무시). setState는 콜백에서만.
  const [state, setState] = useState({ id: null, node: null, error: null })
  const [meta, setMeta] = useState({ id: null, era: null })
  const [rel, setRel] = useState({ id: null, count: null })
  // 양피지 구절 레이어 — { forId, title, ref, textKo, textEn } | null. 인물 변경 시 자동 닫힘.
  const [layerRaw, setLayer] = useState(null)
  const layer = layerRaw?.forId === personId ? layerRaw : null

  useEffect(() => {
    if (!personId) return
    let cancelled = false
    apiGet('/node/' + personId)
      .then(data => { if (!cancelled) setState({ id: personId, node: data, error: null }) })
      .catch(e => { if (!cancelled) setState({ id: personId, node: null, error: e?.status ?? String(e) }) })
    return () => { cancelled = true }
  }, [personId])

  // era·slug는 노드에 없고 /persons/curated에만 존재 — 목록에서 이 인물을 찾는다(헤더 시대 배지·상징물 히어로용).
  useEffect(() => {
    if (!personId) return
    let cancelled = false
    apiGet('/persons/curated')
      .then(list => {
        if (cancelled) return
        const p = list.find(x => x.id === personId)
        setMeta({ id: personId, era: p?.era ?? null, slug: p?.slug ?? null })
      })
      .catch(e => { if (!cancelled) { console.warn('[PersonIntro] 큐레이션 목록 로드 실패', e); setMeta({ id: personId, era: null, slug: null }) } })
    return () => { cancelled = true }
  }, [personId])

  useEffect(() => {
    if (!personId) return
    let cancelled = false
    apiGet(`/person/${personId}/relations`)
      .then(data => { if (!cancelled) setRel({ id: personId, count: (data.relations ?? []).length }) })
      .catch(e => { if (!cancelled) { console.warn('[PersonIntro] 관계 로드 실패', e); setRel({ id: personId, count: null }) } })
    return () => { cancelled = true }
  }, [personId])

  const ready = state.id === personId
  const node = ready ? state.node : null
  const error = ready ? state.error : null

  if (!ready) return <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner color="var(--gold)" /></div>
  if (error) return <p style={{ padding: '1.25rem', fontSize: 14, color: 'var(--danger)' }}>불러오지 못했습니다 ({error})</p>

  const props = node.properties || {}
  const role = props.role
  const intro = props.intro
  const verses = Array.isArray(props.verses) ? props.verses : []
  const traits = Array.isArray(props.traits) ? props.traits : []
  const lifespan = formatLifespan(props.birthYear, props.deathYear)
  const era = meta.id === personId ? meta.era : null
  const relCount = rel.id === personId ? rel.count : null
  // 관문 카운트는 각 도착 탭이 실제로 보여주는 수와 일치시킨다(문↔탭 일치):
  // 여정=정차 수(여정 탭 JourneyList "사건 N개"와 동일), 타임라인=이 인물이 언급된 사건 수
  // (event-ids, 타임라인 personFilter 집합과 동일), 관계=관계 수. journeyStops·personEventIds는 App이 이미 fetch.
  const stopCount = journeyStops ? journeyStops.length : null
  const eventCount = personEventIds ? personEventIds.size : null

  const gateways = [
    { key: 'map', icon: Route, label: '여정', value: stopCount, unit: '개', color: TYPE_COLOR.Place },
    { key: 'timeline', icon: Clock, label: '타임라인', value: eventCount, unit: '건', color: TYPE_COLOR.Event },
    { key: 'relations', icon: Users, label: '관계', value: relCount, unit: '명', color: TYPE_COLOR.Person },
  ]

  const openVerse = v => setLayer({ forId: personId, title: v.ref, ref: v.ref, textKo: v.textKo, textEn: v.textEn })
  const openTrait = t => setLayer({ forId: personId, title: t.trait, ref: t.verse_ref, textKo: t.verse_textKo, textEn: t.verse_textEn })

  return (
    <div style={{ fontFamily: 'var(--sans)', padding: '0 16px' }}>
      {/* 양피지 구절 레이어 — 통일 쉘(VerseLayer, task#202 S1). openVerse/openTrait 공용. */}
      {layer && (
        <VerseLayer
          title={layer.title}
          refLine={layer.ref && layer.ref !== layer.title ? layer.ref : undefined}
          onClose={() => setLayer(null)}
          verseLang={verseLang}
          setVerseLang={setVerseLang}
        >
          {(verseLang === 'ko' ? layer.textKo : layer.textEn)
            ? <div style={paperTextStyle}>{verseLang === 'ko' ? layer.textKo : layer.textEn}</div>
            : <div style={{ fontSize: 13, color: 'var(--paper-accent)' }}>원문이 없습니다</div>}
        </VerseLayer>
      )}

      {/* 상징물 히어로 — 진입마다 대형 선화가 그려지는 시그니처 순간(ADR-0025).
          인물 전환은 App의 key 리마운트로 재재생, reduce는 토큰 붕괴로 즉시 완성. meta 정착 후 렌더(폴백 깜빡임 방지). */}
      {meta.id === personId && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0 2px', color: 'var(--gold)' }}>
          <PersonSymbol slug={meta.slug} size={118} draw />
        </div>
      )}

      {/* 정체성 헤더 — 이름(한/영) · 역할 배지 · era · 생몰 */}
      <div style={{ padding: '16px 0 14px', borderBottom: '1px solid var(--line)' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
          <h2 style={{ margin: 0, fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 24, color: 'var(--ink)', lineHeight: 1.2, letterSpacing: '-0.01em' }}>
            {node.nameKoMissing ? `${node.name} (미번역)` : node.nameKo}
          </h2>
          {!node.nameKoMissing && node.name && node.name !== node.nameKo && (
            <span style={{ fontSize: 14, color: 'var(--ink-faint)' }}>{node.name}</span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
          {role && (
            <span style={{
              fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 999,
              background: 'var(--bg-2)', border: `1px solid ${TYPE_COLOR.Person}`, color: TYPE_COLOR.Person,
            }}>{role}</span>
          )}
          {era && (
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--gold)', letterSpacing: '0.12em', textTransform: 'uppercase', opacity: 0.9 }}>{era}</span>
          )}
          {lifespan && (
            <span style={{ fontSize: 12, color: 'var(--ink-dim)' }}>{lifespan}</span>
          )}
        </div>
      </div>

      {/* 인물 소개문 — 산문 + 근거 구절 칩(양피지 레이어). 모든 산문이 근거 구절과 연결(원칙). */}
      {intro && (
        <div style={{ padding: '16px 0 4px' }}>
          <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.75, color: 'var(--ink)' }}>{intro}</p>
          {verses.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
              {verses.map((v, i) => (
                <button key={i} onClick={() => openVerse(v)} style={chipStyle}>📖 {v.ref}</button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 인물 성품 — SidePanel 성품 섹션 이식(성품 배지 + 📖 구절 칩 → 양피지 레이어 + 설명) */}
      {traits.length > 0 && (
        <div style={{ margin: '18px 0 0', padding: '12px', borderRadius: 8, background: 'var(--bg-2)', border: '1px solid var(--line)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: TYPE_COLOR.Person, marginBottom: 10 }}>인물 성품</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {traits.map((t, i) => (
              <div key={i}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--ink)', background: 'var(--bg-3)', borderRadius: 4, padding: '2px 8px' }}>{t.trait}</span>
                  <button onClick={() => openTrait(t)} style={chipStyle}>📖 {t.verse_ref}</button>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{t.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 관문 요약 — 여정(지도)/사건(타임라인)/관계 탭 점프 */}
      <div style={{ margin: '20px 0 0' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--ink-dim)', marginBottom: 10 }}>더 살펴보기</div>
        <div style={{ display: 'flex', gap: 8 }}>
          {gateways.map(g => {
            const Icon = g.icon
            return (
              <button
                key={g.key}
                onClick={() => onSwitchView(g.key)}
                style={{
                  flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                  padding: '14px 8px', borderRadius: 10, cursor: 'pointer', font: 'inherit',
                  background: 'var(--bg-1)', border: '1px solid var(--line)',
                  transition: 'background var(--dur-fast), border-color var(--dur-fast)',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-2)'; e.currentTarget.style.borderColor = 'var(--line-strong)' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-1)'; e.currentTarget.style.borderColor = 'var(--line)' }}
              >
                <Icon size={20} color={g.color} />
                <span style={{ fontSize: 12, color: 'var(--ink-dim)' }}>{g.label}</span>
                <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--ink)' }}>
                  {g.value == null ? '—' : `${g.value}${g.unit}`}
                </span>
              </button>
            )
          })}
        </div>
        {/* 가계도 — 탭 전환이 아니라 전용 전체화면 스테이지(#/family/<id>)라 관문 카드와 분리한 전체폭 버튼. */}
        <button
          onClick={() => onOpenFamily(personId)}
          style={{
            width: '100%', marginTop: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            padding: '13px 12px', borderRadius: 10, cursor: 'pointer', font: 'inherit',
            background: 'var(--bg-1)', border: '1px solid var(--line)',
            fontSize: 13.5, fontWeight: 700, color: 'var(--ink)',
            transition: 'background var(--dur-fast), border-color var(--dur-fast)',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-2)'; e.currentTarget.style.borderColor = 'var(--line-strong)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-1)'; e.currentTarget.style.borderColor = 'var(--line)' }}
        >
          🌳 <span>가계도 — 조상·자손 보기</span>
        </button>
      </div>
    </div>
  )
}

export default PersonIntro
