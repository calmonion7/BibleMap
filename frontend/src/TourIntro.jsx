import { Route, Clock, Play } from 'lucide-react'
import { TYPE_COLOR } from './theme'
import Spinner from './Spinner'

// 테마 투어 개요(intro) 페이지 — 인물 소개(PersonIntro)의 투어판 축약(task#222).
// 저작돼 있으나 버려지던 subtitle·description을 서사로 노출 + 정차지 목록으로 테마 조망.
// 신규 fetch 없음 — 메타는 App의 /tour 응답, stops는 journeyStops prop 재사용.
const PURPLE = TYPE_COLOR.Book

function TourIntro({ title, subtitle, era, description, journeyStops, onSwitchView = () => {}, onPlay = null }) {
  if (journeyStops == null) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner color={PURPLE} /></div>
  }

  const gateways = [
    { key: 'map', icon: Route, label: '지도로 보기', color: TYPE_COLOR.Place },
    { key: 'timeline', icon: Clock, label: '연표', color: TYPE_COLOR.Event },
  ]

  return (
    <div style={{ fontFamily: 'var(--sans)', padding: '0 16px' }}>
      {/* 히어로 — era 배지(투어 목록 카드와 동일 토큰) + 제목(serif) + 부제 */}
      <div style={{ padding: '24px 0 14px', borderBottom: '1px solid var(--line)' }}>
        {era && (
          <div style={{ color: PURPLE, fontSize: 11, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>{era}</div>
        )}
        <h2 style={{ margin: 0, fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 24, color: 'var(--ink)', lineHeight: 1.2, letterSpacing: '-0.01em' }}>
          {title}
        </h2>
        {subtitle && (
          <p style={{ margin: '8px 0 0', fontSize: 14, color: 'var(--ink-dim)', lineHeight: 1.4 }}>{subtitle}</p>
        )}
      </div>

      {/* 설명 산문 — 인물 intro 산문과 동일 톤 */}
      {description && (
        <div style={{ padding: '16px 0 4px' }}>
          <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.75, color: 'var(--ink)' }}>{description}</p>
        </div>
      )}

      {/* ▶ 투어 재생 CTA — 지도 뷰로 전환해 자동재생 시작(task#223) */}
      {onPlay && journeyStops.length > 0 && (
        <button className="pressable" onClick={onPlay} style={{
          width: '100%', marginTop: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          padding: '13px 12px', borderRadius: 10, cursor: 'pointer', font: 'inherit',
          background: PURPLE, border: 'none', color: '#fff',
          fontSize: 14, fontWeight: 700,
        }}>
          <Play size={16} /> 투어 재생 — 정차지를 따라 여행하기
        </button>
      )}

      {/* 정차지 개요 리스트 — seq · 인물명 · 사건 제목 · 장소 (좌표 없는 stop은 seq 없이) */}
      {journeyStops.length > 0 && (
        <div style={{ margin: '18px 0 0', padding: '12px', borderRadius: 8, background: 'var(--bg-2)', border: '1px solid var(--line)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: PURPLE, marginBottom: 10 }}>정차지 {journeyStops.length}곳</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {journeyStops.map((s, i) => (
              <div key={s.eventId ?? i} style={{ display: 'flex', alignItems: 'baseline', gap: 8, fontSize: 13, lineHeight: 1.5 }}>
                <span style={{ flexShrink: 0, width: 22, textAlign: 'right', fontWeight: 700, color: s.seq != null ? PURPLE : 'var(--ink-faint)', fontVariantNumeric: 'tabular-nums' }}>
                  {s.seq != null ? s.seq : '·'}
                </span>
                <span style={{ minWidth: 0 }}>
                  {s.personNameKo && <span style={{ color: 'var(--gold)', fontWeight: 600 }}>{s.personNameKo} · </span>}
                  <span style={{ color: 'var(--ink)' }}>{s.nameKo}</span>
                  {s.placeNameKo && <span style={{ color: 'var(--ink-faint)' }}> — {s.placeNameKo}</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 관문 카드 — PersonIntro gateway 패턴 축약(지도·연표 2개) */}
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
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)' }}>{g.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default TourIntro
