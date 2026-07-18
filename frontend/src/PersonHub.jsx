import { useState, useEffect, useRef, useLayoutEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import PersonSymbol from './personSymbols'
import { MOBILE_BREAKPOINT } from './constants'
import { saveScroll, loadScroll } from './scrollMemory'

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
const GROUND = 'var(--bg-0)'
const TEXT = 'var(--ink)'
const CARD_BG = 'var(--bg-1)'

// 허브 입장 스태거 — 세션 첫 진입만 재생(복귀는 수십/일 빈도라 반복 재생 금지, 오디트 #4)
let hubEntrancePlayed = false

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

function PersonCard({ person, onSelectPerson, entrance, delayMs }) {
  const [hovered, setHovered] = useState(false)

  return (
    <button
      className={entrance ? 'pressable card-in' : 'pressable'}
      onClick={() => onSelectPerson(person.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      aria-label={`${person.nameKo} — ${person.era} 시대, 사건 ${person.eventCount}건`}
      style={{
        animationDelay: entrance ? `${delayMs}ms` : undefined,
        background: hovered ? 'var(--bg-2)' : CARD_BG,
        border: `1px solid ${hovered ? 'var(--gold-dim)' : 'var(--line)'}`,
        borderRadius: 12,
        padding: '14px 16px 16px',
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
      {/* 상징물 선화 — 입장 시 카드 착지 후 draw-on(ADR-0025), hover 시 선이 또렷해짐 */}
      <span style={{
        alignSelf: 'center',
        color: GOLD,
        opacity: hovered ? 1 : 0.75,
        transition: 'opacity var(--dur-fast)',
        margin: '2px 0 2px',
      }}>
        <PersonSymbol slug={person.slug} size={46} draw={entrance} delayMs={delayMs + 150} />
      </span>

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

function EraSection({ era, persons, onSelectPerson, isFirst, entrance, baseIdx, chapterNo }) {
  const desc = ERA_META[era] || ''

  return (
    <section style={{ marginTop: isFirst ? 0 : 40 }}>
      {/* 섹션 헤더 — 장(章) 표제: 장 번호 + 장식 마름모 + 에라 라벨 + 골드 괘선(펼친 책의 목차 면) */}
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
          display: 'inline-flex',
          alignItems: 'baseline',
          gap: 8,
        }}>
          <span style={{ color: 'var(--ink-faint)', fontSize: 10, letterSpacing: '0.14em' }}>제{chapterNo}장</span>
          <span aria-hidden="true" style={{ fontSize: 8, opacity: 0.7 }}>◆</span>
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
        {persons.map((p, i) => (
          <PersonCard key={p.id} person={p} onSelectPerson={onSelectPerson}
            entrance={entrance} delayMs={Math.min((baseIdx + i) * 30, 400)} />
        ))}
      </div>
    </section>
  )
}

/**
 * PersonHub — 큐레이션 인물 목차(대문) 화면.
 *
 * Props 계약:
 *   onSelectPerson(id: string) — 카드 클릭 시 해당 인물 id 전달
 *
 * 성경책 둘러보기·테마 투어 진입과 테마 토글은 책등 전역 헤더(SpineHeader)로 승격(ADR-0026).
 * 데이터: 내부에서 GET /persons/curated 호출
 *   응답 항목: { id, slug, nameKo, era, eventCount }
 */
export default function PersonHub({ onSelectPerson }) {
  const [persons, setPersons] = useState([])
  // 입장 스태거는 세션 첫 허브 진입에만 — 마운트 시점 값 고정 후 플래그 마킹
  const [entrance] = useState(() => !hubEntrancePlayed)
  useEffect(() => { hubEntrancePlayed = true }, [])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const isMobile = useIsMobile()
  const scrollRef = useRef(null)  // 목록 스크롤 컨테이너 — 위치 복원용(task#214)

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

  // 스크롤 위치 복원 — 목록 렌더(loading=false) 후 콘텐츠 높이 확보 시점에 눌렀던 위치로(task#214).
  useLayoutEffect(() => {
    if (loading) return
    const el = scrollRef.current
    if (el) el.scrollTop = loadScroll('hub')
  }, [loading])

  // 스크롤 위치 캡처 — 스크롤마다 최신값 저장(패시브). 목록 div가 마운트된 뒤(loading=false)에만 부착.
  useEffect(() => {
    if (loading) return
    const el = scrollRef.current
    if (!el) return
    const onScroll = () => saveScroll('hub', el.scrollTop)
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [loading])

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
    <div ref={scrollRef} className={entrance ? 'book-open' : undefined} style={{
      background: GROUND,
      // 지면 질감 — 상단에서 번지는 금박 빛(다크=밤의 서재 촛불, 라이트=양피지 워시). 테마 변수 자동 추종.
      backgroundImage: 'radial-gradient(120% 55% at 50% 0%, color-mix(in srgb, var(--gold) 6%, transparent), transparent 60%)',
      height: '100%',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      {/* 헤더 영역 */}
      <div style={{
        position: 'relative',
        padding: isMobile ? '28px 16px 20px' : '36px 32px 24px',
        borderBottom: '1px solid var(--gold-dim)',
        background: `linear-gradient(180deg, var(--bg-1) 0%, transparent 100%)`,
      }}>
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
          margin: 0,
          lineHeight: 1.5,
        }}>
          인물을 고르면 활동 지역과 사건이 지도에 펼쳐집니다
        </p>
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
            entrance={entrance}
            baseIdx={eras.slice(0, i).reduce((n, e) => n + byEra[e].length, 0)}
            chapterNo={i + 1}
          />
        ))}
      </div>
    </div>
  )
}
