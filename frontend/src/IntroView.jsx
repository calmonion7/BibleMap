import { useEffect, useRef, useState } from 'react'
import PersonSymbol from './personSymbols'
import TourSketch from './tourSketches'

// 사이트 인트로(Site Intro, task#244) — 대문(인물 허브) 앞의 선택적 관문을 시네마틱 오프닝 "필름"으로 재구성.
// 실제 영상 파일이 아니라 무의존 CSS/SVG 오토플레이 연출(ADR-0024: 토큰 참조·transform/opacity·reduced-motion 붕괴).
// 진입하면 4비트가 타이머로 스스로 흘러가고, 끝나면 마지막 비트(도착지 화면)에 정지한다.
// 노출 조건·온오프·딥링크 스킵·ⓘ 재진입은 plan#239 계약 그대로 — 이 컴포넌트 밖(useStageNavigation·SpineHeader)이 소유.
export const INTRO_STORAGE_KEY = 'biblemap-intro'

const prefersReduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

// 마지막 비트(도착지 화면) = 4번째 비트. 애니메이션 duration/easing은 토큰 keyframe에서만 오고,
// 아래 상수는 "장면 체류 시간"일 뿐(plan#239 계약). reduced-motion이면 phase=END로 시작해 이 타이머는 돌지 않는다.
const END = 3
const BEAT_MS = [3000, 5000, 5000] // ① 오프닝 ② 지도+여정선+인장 ③ 시대 몽타주  (총 ~13초, 이후 도착지 정지)

// 몽타주 시대 대표 씬(sketches/ 레지스트리 키, ADR-0029) — 창조 → 출애굽 → 다윗 → 예수 → 초대교회
const ERA_SCENES = [
  'authored-adam-creation',
  'authored-moses-burning-bush',
  'authored-samuel-bethlehem-david-anointing',
  'authored-jesus-bethlehem-birth',
  'authored-peter-pentecost',
]

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

  return (
    <div style={{
      position: 'relative', height: '100%', overflow: 'hidden', background: 'var(--bg-1)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
    }}>
      {phase === 0 && <StarField />}

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

      {/* 비트 레이어 — phase 전환마다 film-in 재생(key). */}
      <div key={phase} className="film-in" style={{
        position: 'relative', zIndex: 1, width: '100%',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        {phase === 0 && <Hero isMobile={isMobile} />}
        {phase === 1 && <MapBeat isMobile={isMobile} />}
        {phase === 2 && <MontageBeat era={era} isMobile={isMobile} />}

        {/* 비트 ④ = 도착지 화면 — 필름이 정지하는 마지막 프레임. 진입점·온오프·ⓘ 안내. */}
        {phase === END && (
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
        )}
      </div>
    </div>
  )
}

const subCta = {
  padding: '9px 18px',
  background: 'color-mix(in srgb, var(--gold) 12%, var(--bg-1))',
  border: '1px solid var(--gold-dim)', borderRadius: 8,
  color: 'var(--gold)', fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, cursor: 'pointer',
}
