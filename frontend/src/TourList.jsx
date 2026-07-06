import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'

// 테마 투어 목록 스테이지 — GET /tours 카드. 카드 클릭 → onSelectTour(id).
// 여러 인물의 여정을 하나의 주제로 엮은 투어를 고르는 화면(인물 허브의 투어판).
const PURPLE = '#a78bfa'
const GROUND = '#11122b'
const TEXT = '#e8e4d8'
const CARD_BG = '#1a1b3a'

export default function TourList({ onSelectTour }) {
  const [tours, setTours] = useState([])
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
  if (error) return <div style={{ color: '#f87171', padding: 24, background: GROUND, height: '100%' }}>테마 투어를 불러오지 못했습니다 — {error}</div>
  if (tours.length === 0) return <div style={{ color: 'rgba(232,228,216,0.45)', padding: 24, background: GROUND, height: '100%' }}>준비된 테마 투어가 없습니다</div>

  return (
    <div style={{ background: GROUND, height: '100%', overflowY: 'auto', boxSizing: 'border-box', padding: '28px 32px 48px' }}>
      <p style={{ color: 'rgba(232,228,216,0.5)', fontSize: 14, margin: '0 0 20px', lineHeight: 1.5 }}>
        여러 인물의 여정을 하나의 주제로 엮어 따라갑니다
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {tours.map(t => (
          <button
            key={t.id}
            onClick={() => onSelectTour(t.id)}
            aria-label={`${t.title} — ${t.era} 시대, 정차지 ${t.stopCount}곳`}
            style={{
              background: CARD_BG, border: `1px solid ${PURPLE}33`, borderRadius: 12,
              padding: '18px 16px', cursor: 'pointer', textAlign: 'left',
              display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0,
            }}
          >
            <span style={{ color: PURPLE, fontSize: 11, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase' }}>{t.era}</span>
            <span style={{ color: TEXT, fontWeight: 700, fontSize: 18, lineHeight: 1.2 }}>{t.title}</span>
            {t.subtitle && <span style={{ color: 'rgba(232,228,216,0.5)', fontSize: 13, lineHeight: 1.4 }}>{t.subtitle}</span>}
            <span style={{ color: 'rgba(232,228,216,0.4)', fontSize: 12, marginTop: 2 }}>정차지 {t.stopCount}곳</span>
          </button>
        ))}
      </div>
    </div>
  )
}
