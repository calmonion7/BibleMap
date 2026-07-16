import { useState, useEffect } from 'react'
import { Sun, Moon } from 'lucide-react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { MOBILE_BREAKPOINT } from './constants'
import { TYPE_COLOR } from './theme'

// 시대 표시 순서 — persons.py _ERA_ORDER와 동일.
const ERA_ORDER = ['원시사', '족장', '출애굽·정복', '사사', '왕국', '선지자', '포로', '신약']

// 시대별 부제 — 카드 그룹 헤더 아래 작은 설명.
const ERA_META = {
  '원시사':      '창조와 홍수, 태초의 사람들',
  '족장':        '창세기의 믿음의 조상들',
  '출애굽·정복': '약속의 땅을 향한 여정',
  '사사':        '혼돈과 구원이 반복된 시대',
  '왕국':        '이스라엘 왕국의 흥망',
  '선지자':      '하나님의 경고와 위로',
  '포로':        '바벨론 포로기의 신앙',
  '신약':        '그리스도와 그 증인들',
}

// 토큰은 전부 CSS 변수 참조 — 테마(다크/라이트) 전환에 자동 추종(ADR-0020)
const GOLD = 'var(--gold)'
const PURPLE = TYPE_COLOR.Book
const GROUND = 'var(--bg-0)'
const TEXT = 'var(--ink)'
const CARD_BG = 'var(--bg-1)'

function useIsMobile() {
  const [mobile, setMobile] = useState(() => window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches)
  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)
    const onChange = (e) => setMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return mobile
}

function PersonCard({ person, onSelectPerson }) {
  const [hovered, setHovered] = useState(false)

  return (
    <button
      className="pressable"
      onClick={() => onSelectPerson(person.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      aria-label={`${person.nameKo} — ${person.era} 시대, 사건 ${person.eventCount}건`}
      style={{
        background: hovered ? 'var(--bg-2)' : CARD_BG,
        border: `1px solid ${hovered ? 'var(--gold-dim)' : 'var(--line)'}`,
        borderRadius: 12,
        padding: '18px 16px',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'background var(--dur-fast), border-color var(--dur-fast), box-shadow var(--dur-fast), transform var(--dur-fast) var(--ease-out)',
        boxShadow: 'var(--shadow-1)',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        minWidth: 0,
      }}
    >
      {/* 이름 */}
      <span style={{
        color: TEXT,
        fontFamily: 'var(--serif)',
        fontWeight: 700,
        fontSize: 18,
        lineHeight: 1.2,
        letterSpacing: '-0.01em',
      }}>
        {person.nameKo}
      </span>

      {/* 시대 */}
      <span style={{
        color: GOLD,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        opacity: 0.85,
      }}>
        {person.era}
      </span>

      {/* 사건 수 */}
      <span style={{
        color: 'var(--ink-dim)',
        fontSize: 12,
        marginTop: 2,
      }}>
        사건 {person.eventCount}
      </span>
    </button>
  )
}

function EraSection({ era, persons, onSelectPerson, isFirst }) {
  const desc = ERA_META[era] || ''

  return (
    <section style={{ marginTop: isFirst ? 0 : 36 }}>
      {/* 섹션 헤더 — 골드 선 + 넓은 자간 에라 라벨 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        marginBottom: 16,
      }}>
        <span style={{
          color: GOLD,
          fontFamily: 'var(--serif)',
          fontWeight: 700,
          fontSize: 12,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          flexShrink: 0,
        }}>
          {era}
        </span>
        <div style={{
          flex: 1,
          height: 1,
          background: 'linear-gradient(to right, var(--gold-dim), var(--line) 60%)',
        }} />
        {desc && (
          <span style={{
            color: 'var(--ink-dim)',
            fontSize: 11,
            letterSpacing: '0.03em',
            flexShrink: 0,
          }}>
            {desc}
          </span>
        )}
      </div>

      {/* 카드 그리드 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap: 10,
      }}>
        {persons.map(p => (
          <PersonCard key={p.id} person={p} onSelectPerson={onSelectPerson} />
        ))}
      </div>
    </section>
  )
}

/**
 * PersonHub — 큐레이션 13인 허브 화면.
 *
 * Props 계약:
 *   onSelectPerson(id: string) — 카드 클릭 시 해당 인물 id 전달
 *   onOpenOverview()            — "성경 책 둘러보기" 버튼 클릭 시 호출
 *   onOpenTours()               — "테마 투어" 버튼 클릭 시 호출
 *
 * 데이터: 내부에서 GET /persons/curated 호출
 *   응답 항목: { id, slug, nameKo, era, eventCount }
 */
export default function PersonHub({ onSelectPerson, onOpenOverview, onOpenTours }) {
  const [persons, setPersons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const isMobile = useIsMobile()
  // 테마 전환은 CSS 변수만 갈아끼우므로 리렌더 불요 — state는 토글 아이콘(해/달) 표시용
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark')
  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    if (next === 'light') document.documentElement.dataset.theme = 'light'
    else delete document.documentElement.dataset.theme
    localStorage.setItem('biblemap-theme', next)
    setTheme(next)
  }

  useEffect(() => {
    // 일시 장애로 허브 전체가 에러 화면에 고착되지 않도록 유한 재시도(1s→2s→4s).
    // 재시도 중엔 스피너 유지, 최종 실패에만 에러 표시.
    let timer, cancelled = false
    const load = attempt => {
      apiGet('/persons/curated')
        .then(data => {
          if (cancelled) return
          setPersons(data)
          setLoading(false)
        })
        .catch(err => {
          if (cancelled) return
          if (attempt < 3) {
            timer = setTimeout(() => load(attempt + 1), 1000 * 2 ** attempt)
          } else {
            setError(err.message || '불러오기 실패')
            setLoading(false)
          }
        })
    }
    load(0)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: GROUND }}>
        <Spinner color={GOLD} />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ color: 'var(--danger)', padding: 24, background: GROUND, height: '100%' }}>
        인물 목록을 불러오지 못했습니다 — {error}
      </div>
    )
  }

  if (persons.length === 0) {
    return (
      <div style={{ color: 'var(--ink-faint)', padding: 24, background: GROUND, height: '100%' }}>
        표시할 인물이 없습니다
      </div>
    )
  }

  // 시대별 그룹핑
  const byEra = {}
  for (const p of persons) {
    if (!byEra[p.era]) byEra[p.era] = []
    byEra[p.era].push(p)
  }
  const eras = ERA_ORDER.filter(e => byEra[e]?.length > 0)

  return (
    <div style={{
      background: GROUND,
      height: '100%',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      {/* 헤더 영역 */}
      <div style={{
        position: 'relative',
        padding: isMobile ? '28px 16px 20px' : '36px 32px 24px',
        borderBottom: '1px solid var(--gold-dim)',
        background: `linear-gradient(180deg, var(--bg-1) 0%, ${GROUND} 100%)`,
      }}>
        {/* 테마 토글 — 라이트(Day Atlas)는 옵트인, 선택은 localStorage 유지(ADR-0020) */}
        <button
          onClick={toggleTheme}
          aria-label={theme === 'light' ? '다크 테마로 전환' : '라이트 테마로 전환'}
          title={theme === 'light' ? '다크 테마로 전환' : '라이트 테마로 전환'}
          style={{
            position: 'absolute',
            top: isMobile ? 24 : 32,
            right: isMobile ? 16 : 32,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 36,
            height: 36,
            borderRadius: '50%',
            border: '1px solid var(--line-strong)',
            background: 'var(--bg-2)',
            color: 'var(--gold)',
            cursor: 'pointer',
          }}
        >
          {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
        </button>
        <h1 style={{
          color: TEXT,
          fontFamily: 'var(--serif)',
          fontSize: isMobile ? 22 : 28,
          fontWeight: 700,
          letterSpacing: '-0.02em',
          margin: '0 0 6px',
          lineHeight: 1.2,
        }}>
          성경 인물 탐험
        </h1>
        <p style={{
          color: 'var(--ink-faint)',
          fontSize: 14,
          margin: '0 0 20px',
          lineHeight: 1.5,
        }}>
          인물을 고르면 활동 지역과 사건이 지도에 펼쳐집니다
        </p>

        {/* 보조 진입 — 성경 책 둘러보기 · 테마 투어 */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            className="pressable"
            onClick={onOpenOverview}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 7,
              padding: '7px 16px',
              border: `1px solid color-mix(in srgb, ${GOLD} 31%, transparent)`,
              borderRadius: 8,
              background: `color-mix(in srgb, ${GOLD} 7%, transparent)`,
              color: GOLD,
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              letterSpacing: '0.03em',
              transition: 'background var(--dur-fast), border-color var(--dur-fast), transform var(--dur-fast) var(--ease-out)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = `color-mix(in srgb, ${GOLD} 13%, transparent)`
              e.currentTarget.style.borderColor = `color-mix(in srgb, ${GOLD} 56%, transparent)`
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = `color-mix(in srgb, ${GOLD} 7%, transparent)`
              e.currentTarget.style.borderColor = `color-mix(in srgb, ${GOLD} 31%, transparent)`
            }}
          >
            <span style={{ fontSize: 15 }}>📖</span>
            성경 책 둘러보기
          </button>
          <button
            className="pressable"
            onClick={onOpenTours}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 7,
              padding: '7px 16px',
              border: `1px solid color-mix(in srgb, ${PURPLE} 31%, transparent)`,
              borderRadius: 8,
              background: `color-mix(in srgb, ${PURPLE} 7%, transparent)`,
              color: PURPLE,
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              letterSpacing: '0.03em',
              transition: 'background var(--dur-fast), border-color var(--dur-fast), transform var(--dur-fast) var(--ease-out)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = `color-mix(in srgb, ${PURPLE} 13%, transparent)`
              e.currentTarget.style.borderColor = `color-mix(in srgb, ${PURPLE} 56%, transparent)`
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = `color-mix(in srgb, ${PURPLE} 7%, transparent)`
              e.currentTarget.style.borderColor = `color-mix(in srgb, ${PURPLE} 31%, transparent)`
            }}
          >
            <span style={{ fontSize: 15 }}>🧭</span>
            테마 투어
          </button>
        </div>
      </div>

      {/* 시대별 카드 그룹 */}
      <div style={{
        padding: isMobile ? '20px 16px 32px' : '28px 32px 48px',
      }}>
        {eras.map((era, i) => (
          <EraSection
            key={era}
            era={era}
            persons={byEra[era]}
            onSelectPerson={onSelectPerson}
            isFirst={i === 0}
          />
        ))}
      </div>
    </div>
  )
}
