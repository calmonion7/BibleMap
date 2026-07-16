import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { TYPE_COLOR } from './theme'

// 테마 투어 목록 스테이지 — GET /tours 카드. 카드 클릭 → onSelectTour(id).
// 여러 인물의 여정을 하나의 주제로 엮은 투어를 고르는 화면(인물 허브의 투어판).
// Night Atlas 토큰(design-direction.md) — 보라는 theme.js 상수, 표면·잉크는 CSS 변수 참조
const PURPLE = TYPE_COLOR.Book
const GROUND = 'var(--bg-0)'
const TEXT = 'var(--ink)'
const CARD_BG = 'var(--bg-1)'

// 입장 스태거 — 세션 첫 진입만(허브 hubEntrancePlayed와 동일 패턴)
let toursEntrancePlayed = false

function TourCard({ tour, onSelectTour, entrance, delayMs }) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      className={entrance ? 'pressable card-in' : 'pressable'}
      onClick={() => onSelectTour(tour.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      aria-label={`${tour.title} — ${tour.era} 시대, 정차지 ${tour.stopCount}곳`}
      style={{
        animationDelay: entrance ? `${delayMs}ms` : undefined,
        background: hovered ? 'var(--bg-2)' : CARD_BG,
        border: `1px solid color-mix(in srgb, ${PURPLE} ${hovered ? 45 : 20}%, transparent)`,
        borderRadius: 12,
        padding: '18px 16px', cursor: 'pointer', textAlign: 'left',
        transition: 'background var(--dur-fast), border-color var(--dur-fast), transform var(--dur-fast) var(--ease-out)',
        display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0,
      }}
    >
      <span style={{ color: PURPLE, fontSize: 11, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase' }}>{tour.era}</span>
      <span style={{ color: TEXT, fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 18, lineHeight: 1.2 }}>{tour.title}</span>
      {tour.subtitle && <span style={{ color: 'var(--ink-dim)', fontSize: 13, lineHeight: 1.4 }}>{tour.subtitle}</span>}
      <span style={{ color: 'var(--ink-dim)', fontSize: 12, marginTop: 2 }}>정차지 {tour.stopCount}곳</span>
    </button>
  )
}

export default function TourList({ onSelectTour }) {
  const [tours, setTours] = useState([])
  const [entrance] = useState(() => !toursEntrancePlayed)
  useEffect(() => { toursEntrancePlayed = true }, [])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    apiGet('/tours')
      .then(data => { if (!cancelled) { setTours(data); setLoading(false) } })
      .catch(err => { if (!cancelled) { setError(err.message || '불러오기 실패'); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: GROUND }}><Spinner color={PURPLE} /></div>
  if (error) return <div style={{ color: 'var(--danger)', padding: 24, background: GROUND, height: '100%' }}>테마 투어를 불러오지 못했습니다 — {error}</div>
  if (tours.length === 0) return <div style={{ color: 'var(--ink-faint)', padding: 24, background: GROUND, height: '100%' }}>준비된 테마 투어가 없습니다</div>

  return (
    <div style={{ background: GROUND, height: '100%', overflowY: 'auto', boxSizing: 'border-box', padding: '28px 32px 48px' }}>
      <p style={{ color: 'var(--ink-dim)', fontSize: 14, margin: '0 0 20px', lineHeight: 1.5 }}>
        여러 인물의 여정을 하나의 주제로 엮어 따라갑니다
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {tours.map((t, i) => (
          <TourCard key={t.id} tour={t} onSelectTour={onSelectTour}
            entrance={entrance} delayMs={Math.min(i * 30, 400)} />
        ))}
      </div>
    </div>
  )
}
