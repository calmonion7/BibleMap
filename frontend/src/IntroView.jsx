import { useEffect, useRef, useState } from 'react'
import { UserRound, Route, Clock, Users, HeartHandshake, Network, BookOpen, BarChart3, ScrollText } from 'lucide-react'
import PersonSymbol from './personSymbols'
import TourSketch from './tourSketches'

// 사이트 인트로(Site Intro, task#244) — 대문(인물 허브) 앞의 선택적 관문을 시네마틱 오프닝 "필름"으로 재구성.
// 실제 영상 파일이 아니라 무의존 CSS/SVG 오토플레이 연출(ADR-0024: 토큰 참조·transform/opacity·reduced-motion 붕괴).
// 진입하면 4비트가 타이머로 스스로 흘러가고, 끝나면 마지막 비트(도착지 화면)에 정지한다.
// 노출 조건·온오프·딥링크 스킵·ⓘ 재진입은 plan#239 계약 그대로 — 이 컴포넌트 밖(useStageNavigation·SpineHeader)이 소유.
export const INTRO_STORAGE_KEY = 'biblemap-intro'

const prefersReduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

// 마지막 비트(도착지 화면). 애니메이션 duration/easing은 토큰 keyframe에서만 오고, 아래 상수는
// "장면 체류 시간"일 뿐(plan#239 계약). reduced-motion이면 phase=END로 시작해 이 타이머는 돌지 않는다.
// 컨텐츠 소개는 상단 메뉴별 장면(인물·성경책·투어)을 각각 별도 비트로 둬 비트 순차 전환(겹침 없음)을 그대로 탄다.
const END = 6
const BEAT_MS = [3000, 5000, 5000, 3000, 3000, 3000] // ①오프닝 ②지도+여정+인장 ③시대 몽타주 ④인물 메뉴 ⑤성경책 메뉴 ⑥투어 메뉴 (총 ~20초, 이후 도착지 정지)
// 비트 전환 — 장면이 "겹치지" 않게 순차 디졸브: 이전 비트가 먼저 페이드아웃(--dur-base≈250ms) 한 뒤
// 새 비트가 지연 후 페이드인(--dur-slow≈400ms). 동시 노출(이중노출) 없이 배경을 통해 부드럽게 교체.
const BEAT_IN_DELAY = 260 // 새 비트 페이드인 시작 지연 = 이전 비트 페이드아웃이 끝난 직후
const TRANS_MS = 700      // 전환 총 길이(페이드아웃 + 지연 + 페이드인) 후 이전 레이어 제거

// 몽타주 시대 대표 씬(sketches/ 레지스트리 키, ADR-0029) — 창조 → 출애굽 → 다윗 → 예수 → 초대교회
const ERA_SCENES = [
  'authored-adam-creation',
  'authored-moses-burning-bush',
  'authored-samuel-bethlehem-david-anointing',
  'authored-jesus-bethlehem-birth',
  'authored-peter-pentecost',
]

// 컨텐츠 소개 장면(task#245) — 실제 상단 메뉴(인물·성경책·투어) 기준으로 "무슨 정보를 얻는지"를 두괄식으로
// 먼저 말하고, 그 아래 실제 하위 메뉴를 앱과 똑같은 lucide 아이콘+라벨로 보여줘 어떤 컨텐츠가 있는지 인지시킨다.
const SCENES = [
  {
    nav: '인물',
    art: 'person',
    lead: '성경 인물의 일생을 통째로',
    sub: '발자취 · 연대 · 관계 · 믿음 · 계보까지 한 인물을 깊이',
    tabs: [[UserRound, '소개'], [Route, '여정'], [Clock, '연표'], [Users, '관계'], [HeartHandshake, '의존'], [Network, '족보']],
  },
  {
    nav: '성경책',
    art: 'books',
    lead: '성경 66권을 한눈에',
    sub: '권별 주제 · 핵심 인물 · 지도, 그리고 단어의 분포까지',
    tabs: [[BookOpen, '책 둘러보기'], [BarChart3, '단어 분포']],
  },
  {
    nav: '투어',
    art: 'tour',
    lead: '이야기를 따라 자동으로',
    sub: '테마별 여정을 지도 · 연표와 함께 재생',
    tabs: [[ScrollText, '개요'], [Route, '여정'], [Clock, '연표']],
  },
]

// 장면 설명 선화(thread-draw/film-fade) — 메뉴 앞 지도·몽타주 애니메이션과 같은 톤으로 각 메뉴를 "그려서" 설명.
function SceneArt({ art, isMobile }) {
  const h = isMobile ? 72 : 92
  const common = { viewBox: '0 0 120 80', height: h, 'aria-hidden': true, fill: 'none', stroke: 'var(--gold)', strokeLinecap: 'round', strokeLinejoin: 'round' }
  if (art === 'person')
    return (
      <svg {...common}>
        {/* 삶의 궤적(뒤, 옅게 그려짐) */}
        <path className="thread-draw" style={{ '--thread-delay': '120ms' }} pathLength="1" d="M12 64 Q 40 40 62 52 T 108 32" stroke="var(--gold-dim)" strokeWidth="1.6" />
        {/* 사람(선화 draw) */}
        <g strokeWidth="2.2">
          <circle className="thread-draw" style={{ '--thread-delay': '440ms' }} pathLength="1" cx="60" cy="26" r="9" />
          <path className="thread-draw" style={{ '--thread-delay': '640ms' }} pathLength="1" d="M60 35 V58 M60 41 L47 50 M60 41 L73 50 M60 58 L50 72 M60 58 L70 72" />
        </g>
      </svg>
    )
  if (art === 'books')
    return (
      <svg {...common} strokeWidth="2.2">
        {/* 책등이 나란히 서는 서가(스태거 라이즈) */}
        {[0, 1, 2, 3, 4].map(i => (
          <rect key={i} className="film-fade" style={{ animationDelay: `${180 + i * 110}ms` }}
            x={28 + i * 13} y={26 + (i % 2 ? 5 : 0)} width="9" height={44 - (i % 2 ? 5 : 0)} rx="2" />
        ))}
      </svg>
    )
  // tour — 미니 경로 그려지고 정차지·재생 삼각형 등장
  return (
    <svg {...common}>
      <path d="M8 62 q20 -6 40 -3 q18 -8 40 -4 q12 -1 24 -6" stroke="var(--ink-faint)" strokeWidth="1.3" opacity="0.5" />
      <path className="thread-draw" style={{ '--thread-delay': '220ms' }} pathLength="1" d="M20 56 Q 46 28 66 42 T 104 26" strokeWidth="2.2" />
      <g className="film-fade" style={{ animationDelay: '980ms' }} fill="var(--gold)" stroke="none">
        {[[50, 37], [80, 40], [104, 26]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="3" />)}
      </g>
      <g className="film-fade" style={{ animationDelay: '1180ms' }}>
        <circle cx="20" cy="56" r="7.5" strokeWidth="1.8" />
        <path d="M17 51.5 L25.5 56 L17 60.5 Z" fill="var(--gold)" stroke="none" />
      </g>
    </svg>
  )
}

// 밤하늘 — 좌표 고정(재생마다 흔들리지 않게 랜덤 금지).
const STARS = [[12, 18], [24, 42], [38, 12], [52, 30], [66, 20], [78, 46], [88, 14], [16, 66], [34, 74], [70, 68], [84, 60], [48, 56]]
function StarField() {
  return (
    <svg viewBox="0 0 100 80" preserveAspectRatio="xMidYMid slice" aria-hidden="true"
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
      {STARS.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={i % 3 === 0 ? 0.5 : 0.3} fill="var(--gold)" opacity={0.25 + (i % 4) * 0.14} />
      ))}
    </svg>
  )
}

// 공용 히어로(오프닝·도착지 공통) — 도착지에서 오프닝의 타이틀이 이어지는 연속감.
function Hero({ isMobile }) {
  return (
    <>
      <h1 className="intro-rise" style={{
        margin: 0, fontFamily: 'var(--serif-display)', fontWeight: 400,
        fontSize: isMobile ? 42 : 60, letterSpacing: '0.01em', lineHeight: 1.1,
      }}>
        <span style={{ color: 'var(--ink)' }}>Bible</span>
        <span style={{ color: 'var(--gold)' }}>Map</span>
      </h1>
      <div className="intro-line" style={{
        width: isMobile ? 150 : 220, height: 1, margin: '18px 0',
        background: 'var(--gold-dim)', animationDelay: '200ms',
      }} />
      <p className="intro-rise" style={{
        margin: 0, fontFamily: 'var(--serif)', fontSize: isMobile ? 15 : 17,
        color: 'var(--ink-dim)', letterSpacing: '0.04em', animationDelay: '320ms',
      }}>
        성경 인물·장소·사건의 지도
      </p>
    </>
  )
}

// 비트 ② — 지도 위에 여정선이 그려지고(thread-draw), 정차지 점이 뜨고, 인물 인장이 그려진다(symbol-draw).
function MapBeat({ isMobile }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: isMobile ? 16 : 22, width: '100%', maxWidth: 560, padding: '0 20px' }}>
      <div className="intro-rise" style={{ fontFamily: 'var(--serif)', fontSize: isMobile ? 14 : 16, color: 'var(--ink-dim)', letterSpacing: '0.04em' }}>
        지도 위에서 인물의 발자취를 따라
      </div>
      <svg viewBox="0 0 120 80" width="100%" aria-hidden="true" fill="none"
        stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block', maxWidth: 460 }}>
        {/* 손그림 해안선(원경, 정적 옅은 선) — 지도임을 암시 */}
        <g stroke="var(--ink-faint)" strokeWidth="1.1" opacity="0.55">
          <path d="M4 60 q18 -6 30 -3 q10 -8 24 -4 q14 -10 30 -3 q12 -2 24 -8" />
          <path d="M10 70 q24 -5 44 -6 q22 -1 52 -7" opacity="0.6" />
          <path d="M78 30 q8 -3 14 1 q6 -4 12 0" opacity="0.5" />
        </g>
        {/* 여정선 — 손으로 그려지듯(thread-draw, pathLength=1). 딜레이 후 그려짐 */}
        <path d="M18 62 Q 42 34 62 46 T 104 24" pathLength="1" className="thread-draw"
          style={{ '--thread-delay': '500ms' }} stroke="var(--gold)" strokeWidth="1.8" />
        {/* 정차지 점 — 선이 그려진 뒤 페이드인 */}
        <g className="film-fade" style={{ animationDelay: '1400ms' }} fill="var(--gold)" stroke="none">
          {[[18, 62], [50, 40], [78, 43], [104, 24]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="1.8" />
          ))}
        </g>
      </svg>
      {/* 인물 인장 — 여정 끝에서 선화가 그려짐(symbol-draw) */}
      <div className="film-fade" style={{ animationDelay: '1800ms', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, color: 'var(--gold)' }}>
        <PersonSymbol slug="david" size={isMobile ? 56 : 72} draw />
        <span style={{ fontFamily: 'var(--serif)', fontSize: 13, color: 'var(--ink-dim)', letterSpacing: '0.06em' }}>다윗</span>
      </div>
    </div>
  )
}

// 비트 ③ — 시대 스케치 몽타주. 각 씬은 reduce 정적 렌더로 크로스페이드(개별 씬의 SMIL 안무는 몽타주엔 과함).
function MontageBeat({ era, isMobile }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: isMobile ? 14 : 18, width: '100%', maxWidth: 520, padding: '0 20px' }}>
      <div className="intro-rise" style={{ fontFamily: 'var(--serif-display)', fontSize: isMobile ? 20 : 24, color: 'var(--ink)', letterSpacing: '0.02em' }}>
        창조에서 초대교회까지
      </div>
      {/* 양피지 카드 — 투어 스케치 관용구(TourSketchPanel 톤) */}
      <div key={era} className="film-fade" style={{
        width: '100%', maxWidth: isMobile ? 320 : 420, aspectRatio: '120 / 64',
        background: 'var(--paper)', color: 'var(--paper-ink)',
        border: '1px solid color-mix(in srgb, var(--paper-accent) 40%, transparent)', borderRadius: 10,
        overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <TourSketch eventId={ERA_SCENES[era]} width="100%" reduce />
      </div>
    </div>
  )
}

// 컨텐츠 소개 장면 — 상단 메뉴 하나(인물/성경책/투어)를 두괄식으로: 메뉴 이름 → 얻는 것(헤드라인) →
// 무슨 정보인지(부제) → 실제 하위 메뉴(앱과 동일한 lucide 아이콘 + 라벨). 프레임 없이 콘텐츠만.
function MenuScene({ scene, isMobile }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: isMobile ? 9 : 13, width: '100%', maxWidth: 600, padding: '0 22px' }}>
      <div style={{ marginBottom: isMobile ? 2 : 6 }}><SceneArt art={scene.art} isMobile={isMobile} /></div>
      <div className="intro-rise" style={{ fontFamily: 'var(--serif)', fontSize: isMobile ? 12 : 13, letterSpacing: '0.18em', color: 'var(--gold)' }}>
        {scene.nav}
      </div>
      <div className="intro-rise" style={{ animationDelay: '90ms', fontFamily: 'var(--serif-display)', fontSize: isMobile ? 30 : 42, color: 'var(--ink)', lineHeight: 1.12, letterSpacing: '0.01em' }}>
        {scene.lead}
      </div>
      <div className="intro-rise" style={{ animationDelay: '190ms', fontFamily: 'var(--serif)', fontSize: isMobile ? 13.5 : 16, color: 'var(--ink-dim)', letterSpacing: '0.02em' }}>
        {scene.sub}
      </div>
      <div style={{ display: 'flex', gap: isMobile ? 14 : 26, flexWrap: 'wrap', justifyContent: 'center', marginTop: isMobile ? 10 : 18, maxWidth: 480 }}>
        {scene.tabs.map(([Icon, label], i) => (
          <div key={label} className="intro-rise" style={{ animationDelay: `${330 + i * 90}ms`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7, color: 'var(--gold)' }}>
            <Icon size={isMobile ? 24 : 28} strokeWidth={1.6} />
            <span style={{ fontFamily: 'var(--serif)', fontSize: isMobile ? 12 : 13.5, color: 'var(--ink-dim)', whiteSpace: 'nowrap' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// 비트 ⑤ = 도착지 화면 — 필름이 정지하는 마지막 프레임. 진입점·온오프·ⓘ 안내.
function Destination({ isMobile, onStart, onOpenTours, onOpenOverview, hidden, toggleHidden }) {
  return (
    <div style={{ width: '100%', maxWidth: 560, padding: '0 22px' }}>
      <Hero isMobile={isMobile} />
      <div className="intro-rise" style={{ marginTop: isMobile ? 30 : 40, animationDelay: '440ms' }}>
        <button className="pressable" onClick={onStart} style={{
          padding: isMobile ? '13px 34px' : '15px 44px',
          background: 'var(--gold)', border: 'none', borderRadius: 10,
          color: 'var(--bg-1)', fontFamily: 'var(--serif)', fontWeight: 700,
          fontSize: isMobile ? 15 : 16, letterSpacing: '0.06em', cursor: 'pointer',
        }}>
          탐험 시작하기
        </button>
      </div>
      <div className="intro-rise" style={{
        marginTop: 18, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', animationDelay: '560ms',
      }}>
        <button className="pressable" onClick={onOpenTours} style={subCta}>테마 투어 보기</button>
        <button className="pressable" onClick={onOpenOverview} style={subCta}>성경 책 둘러보기</button>
      </div>
      <div className="intro-rise" style={{ marginTop: 26, animationDelay: '680ms' }}>
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, color: 'var(--ink-dim)', cursor: 'pointer' }}>
          <input type="checkbox" checked={hidden} onChange={toggleHidden} style={{ accentColor: 'var(--gold)' }} />
          인트로 다시 보지 않기
        </label>
        <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--ink-faint)' }}>
          꺼도 상단의 ⓘ 소개 버튼으로 언제든 다시 볼 수 있어요.
        </div>
      </div>
    </div>
  )
}

// 한 비트의 내용 렌더 — 오프닝은 밤하늘(StarField)을 함께 담아 전환에 같이 실린다.
// 비트 3~5 = 상단 메뉴별 컨텐츠 소개 장면(인물·성경책·투어), 6 = 도착지.
function renderBeat(p, ctx) {
  if (p === 0) return <><StarField /><Hero isMobile={ctx.isMobile} /></>
  if (p === 1) return <MapBeat isMobile={ctx.isMobile} />
  if (p === 2) return <MontageBeat era={ctx.era} isMobile={ctx.isMobile} />
  if (p >= 3 && p <= 5) return <MenuScene scene={SCENES[p - 3]} isMobile={ctx.isMobile} />
  return <Destination {...ctx} />
}

export default function IntroView({ onStart, onOpenTours, onOpenOverview, isMobile }) {
  // 온오프 — 끄면 무해시 진입이 허브 직행. 켠 상태 값은 키 제거(기본 켜짐과 동일 상태).
  const [hidden, setHidden] = useState(() => localStorage.getItem(INTRO_STORAGE_KEY) === 'off')
  const toggleHidden = () => {
    const next = !hidden
    if (next) localStorage.setItem(INTRO_STORAGE_KEY, 'off')
    else localStorage.removeItem(INTRO_STORAGE_KEY)
    setHidden(next)
  }

  // 필름 진행 — reduced-motion이면 필름을 건너뛰고 도착지 화면부터.
  const [phase, setPhase] = useState(() => (prefersReduced() ? END : 0))
  const [era, setEra] = useState(0)
  const timers = useRef([])
  const clearTimers = () => { timers.current.forEach(clearTimeout); timers.current = [] }

  // 비트 전환 레이어 — phase가 바뀌면 이전 레이어는 페이드아웃(exiting)으로 표시하고, 새 레이어는
  // 지연 페이드인(delay)으로 얹는다. 둘의 불투명도가 시차라 동시에 보이지 않는다(겹침 없음). TRANS_MS 뒤 정리.
  const [layers, setLayers] = useState(() => [{ p: phase, id: 0, delay: 0 }])
  const beatId = useRef(0)
  const firstBeat = useRef(true)
  useEffect(() => {
    if (firstBeat.current) { firstBeat.current = false; return } // 최초 레이어는 이미 스택에 있음(마운트 페이드인)
    beatId.current += 1
    const id = beatId.current
    setLayers(ls => [...ls.map(l => ({ ...l, exiting: true })), { p: phase, id, delay: BEAT_IN_DELAY }])
    const t = setTimeout(() => setLayers([{ p: phase, id, delay: 0, settled: true }]), TRANS_MS)
    return () => clearTimeout(t)
  }, [phase])

  useEffect(() => {
    if (prefersReduced()) return
    let acc = 0
    BEAT_MS.forEach((ms, i) => {
      acc += ms
      timers.current.push(setTimeout(() => setPhase(i + 1), acc))
    })
    return clearTimers
  }, [])

  // 몽타주 비트 동안 시대 대표 씬 순환.
  useEffect(() => {
    if (phase !== 2 || prefersReduced()) return
    const per = Math.floor(BEAT_MS[2] / ERA_SCENES.length)
    const t = ERA_SCENES.map((_, i) => setTimeout(() => setEra(i), i * per))
    return () => t.forEach(clearTimeout)
  }, [phase])

  const skip = () => { clearTimers(); setPhase(END) }

  const ctx = { isMobile, era, onStart, onOpenTours, onOpenOverview, hidden, toggleHidden }

  return (
    <div style={{
      position: 'relative', height: '100%', overflow: 'hidden', background: 'var(--bg-1)', textAlign: 'center',
    }}>
      {/* 건너뛰기 — 재생 내내 상시 노출(정지+종료 겸함). 도착지에선 숨김. */}
      {phase !== END && (
        <button className="pressable" onClick={skip} style={{
          position: 'absolute', top: 16, right: 16, zIndex: 2,
          padding: '7px 14px', background: 'color-mix(in srgb, var(--bg-2) 80%, transparent)',
          border: '1px solid var(--line)', borderRadius: 8,
          color: 'var(--ink-dim)', fontFamily: 'var(--serif)', fontSize: 12.5, cursor: 'pointer',
        }}>
          건너뛰기 →
        </button>
      )}

      {/* 비트 레이어 — 이전 비트(exiting) 페이드아웃 → 새 비트(delay) 페이드인. 시차라 겹쳐 보이지 않는다. */}
      {layers.map(({ p, id, delay, exiting, settled }) => (
        <div key={id} className={exiting ? 'beat-out' : settled ? undefined : 'beat-in'} style={{
          position: 'absolute', inset: 0, zIndex: 1,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          animationDelay: delay ? `${delay}ms` : undefined,
        }}>
          {renderBeat(p, ctx)}
        </div>
      ))}
    </div>
  )
}

const subCta = {
  padding: '9px 18px',
  background: 'color-mix(in srgb, var(--gold) 12%, var(--bg-1))',
  border: '1px solid var(--gold-dim)', borderRadius: 8,
  color: 'var(--gold)', fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, cursor: 'pointer',
}
