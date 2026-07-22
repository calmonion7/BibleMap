import { useEffect, useRef, useState } from 'react'
import { Route, Compass, BookOpen, Network, ScrollText } from 'lucide-react'
import PersonSymbol from './personSymbols'

// 사이트 인트로(Site Intro, task#239) — 대문(인물 허브) 앞의 선택적 관문 화면.
// 무해시 진입 + 켜짐(localStorage 'biblemap-intro' !== 'off')일 때만 허브보다 먼저 보인다(useStageNavigation).
// 모션은 ADR-0024 계약(토큰 참조·transform/opacity·reduced-motion 토큰 붕괴) 안에서만.
export const INTRO_STORAGE_KEY = 'biblemap-intro'

// 스크롤 리빌 — 뷰포트 진입 1회 감지(.intro-sec → .intro-seen). 재생 후 관찰 해제.
function useReveal() {
  const ref = useRef(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setSeen(true); io.disconnect() }
    }, { threshold: 0.2 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return [ref, seen]
}

// 섹션 카드 — 리빌 시 본체 rise + 자식 스태거. visual은 리빌 후 마운트(심볼 draw가 화면 안에서 재생되게).
function IntroSection({ visual, title, copy, cta, onCta, isMobile }) {
  const [ref, seen] = useReveal()
  return (
    <section
      ref={ref}
      className={`intro-sec${seen ? ' intro-seen' : ''}`}
      style={{
        display: 'flex', gap: isMobile ? 14 : 22, alignItems: 'flex-start',
        background: 'var(--bg-2)', border: '1px solid var(--line)',
        borderRadius: 12, padding: isMobile ? '18px 16px' : '24px 26px',
      }}
    >
      <div style={{
        width: isMobile ? 52 : 72, height: isMobile ? 52 : 72, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        borderRadius: '50%', border: '1px solid var(--gold-dim)',
        background: 'color-mix(in srgb, var(--gold) 7%, transparent)',
        color: 'var(--gold)',
      }}>
        {seen && visual}
      </div>
      <div style={{ minWidth: 0 }}>
        <h2 className={seen ? 'intro-rise' : undefined} style={{
          margin: '2px 0 8px', fontFamily: 'var(--serif-display)', fontWeight: 400,
          fontSize: isMobile ? 19 : 22, color: 'var(--ink)', letterSpacing: '0.01em',
          animationDelay: '80ms',
        }}>
          {title}
        </h2>
        <p className={seen ? 'intro-rise' : undefined} style={{
          margin: 0, fontFamily: 'var(--serif)', fontSize: isMobile ? 13.5 : 14.5,
          lineHeight: 1.75, color: 'var(--ink-dim)', animationDelay: '180ms',
        }}>
          {copy}
        </p>
        {cta && (
          <button
            className={`pressable${seen ? ' intro-rise' : ''}`}
            onClick={onCta}
            style={{
              marginTop: 14, padding: '8px 16px',
              background: 'color-mix(in srgb, var(--gold) 14%, var(--bg-1))',
              border: '1px solid var(--gold-dim)', borderRadius: 8,
              color: 'var(--gold)', fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700,
              cursor: 'pointer', animationDelay: '280ms',
            }}
          >
            {cta} →
          </button>
        )}
      </div>
    </section>
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

  const iconSize = isMobile ? 26 : 34

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-1)' }}>
      <div style={{ maxWidth: 720, margin: '0 auto', padding: isMobile ? '0 18px 48px' : '0 28px 64px' }}>

        {/* 히어로 — 상단 정적 스태거 입장(관찰 불요) */}
        <div style={{
          minHeight: isMobile ? '52vh' : '58vh',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', paddingTop: 24,
        }}>
          <h1 className="intro-rise" style={{
            margin: 0, fontFamily: 'var(--serif-display)', fontWeight: 400,
            fontSize: isMobile ? 40 : 56, letterSpacing: '0.01em', lineHeight: 1.1,
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
          <p className="intro-rise" style={{
            margin: '14px 0 0', fontFamily: 'var(--serif)', fontSize: isMobile ? 13 : 14,
            lineHeight: 1.8, color: 'var(--ink-faint)', maxWidth: 480, animationDelay: '440ms',
          }}>
            창조에서 초대교회까지 — 인물의 발자취를 지도 위에서 따라가고,
            모든 이야기를 성경 구절 그대로 확인하는 탐험 지도입니다.
          </p>
          <div className="intro-rise" style={{
            marginTop: 34, color: 'var(--ink-faint)', fontSize: 12, letterSpacing: '0.12em',
            animationDelay: '560ms',
          }}>
            아래로 살펴보기 ▾
          </div>
        </div>

        {/* 기능 소개 6섹션 — 스크롤 리빌 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? 14 : 18 }}>
          <IntroSection
            isMobile={isMobile}
            visual={<PersonSymbol slug="david" size={iconSize + 14} draw />}
            title="인물 탐험"
            copy="아브라함·다윗·바울 — 성경의 인물들을 시대별 목차에서 만납니다. 인물마다 손으로 그린 인장과 함께 생애·성품·소개가 근거 구절과 나란히 펼쳐집니다."
            cta="인물 목차 열기"
            onCta={onStart}
          />
          <IntroSection
            isMobile={isMobile}
            visual={<Route size={iconSize} strokeWidth={1.4} />}
            title="여정 지도"
            copy="한 인물의 발자취가 실제 지도 위 여정선으로 이어집니다. 정차지를 하나씩 밟으며 그 자리에서 일어난 사건과 말씀을 함께 읽습니다."
            cta="여정 시작하기"
            onCta={onStart}
          />
          <IntroSection
            isMobile={isMobile}
            visual={<Compass size={iconSize} strokeWidth={1.4} />}
            title="테마 투어"
            copy="창조에서 초대교회까지 아홉 갈래의 주제 투어. 정차지마다 양피지 위에 그려지는 장면 스케치가 이야기의 흐름을 안내합니다."
            cta="투어 보기"
            onCta={onOpenTours}
          />
          <IntroSection
            isMobile={isMobile}
            visual={<BookOpen size={iconSize} strokeWidth={1.4} />}
            title="성경 책 둘러보기"
            copy="66권을 장르와 시대로 한눈에 훑고, 책마다 배경·주요 인물·지도를 살핍니다. 장별 본문 읽기와 단어 분포까지 한 책의 안팎을 모두 담았습니다."
            cta="성경책 펼치기"
            onCta={onOpenOverview}
          />
          <IntroSection
            isMobile={isMobile}
            visual={<Network size={iconSize} strokeWidth={1.4} />}
            title="가계도"
            copy="아담에서 뻗어 나온 혈통의 가지들을 나무로 봅니다. 인물 상세에서 족보로 들어가면 조상과 후손이 한 화면에 이어집니다."
          />
          <IntroSection
            isMobile={isMobile}
            visual={<ScrollText size={iconSize} strokeWidth={1.4} />}
            title="말씀이 근거입니다"
            copy="이 지도의 모든 서술은 성경 구절을 근거로 답니다. 화면의 어떤 진술이든 곁에 붙은 근거 절을 눌러 본문을 한글·영어로 바로 확인할 수 있습니다."
          />
        </div>

        {/* 마무리 CTA + 온오프 */}
        <div style={{ textAlign: 'center', marginTop: isMobile ? 36 : 48 }}>
          <button
            className="pressable"
            onClick={onStart}
            style={{
              padding: isMobile ? '13px 34px' : '15px 44px',
              background: 'var(--gold)', border: 'none', borderRadius: 10,
              color: 'var(--bg-1)', fontFamily: 'var(--serif)', fontWeight: 700,
              fontSize: isMobile ? 15 : 16, letterSpacing: '0.06em', cursor: 'pointer',
            }}
          >
            탐험 시작하기
          </button>
          <div style={{ marginTop: 22 }}>
            <label style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              fontSize: 12.5, color: 'var(--ink-dim)', cursor: 'pointer',
            }}>
              <input type="checkbox" checked={hidden} onChange={toggleHidden} style={{ accentColor: 'var(--gold)' }} />
              인트로 다시 보지 않기
            </label>
            <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--ink-faint)' }}>
              꺼도 상단의 ⓘ 소개 버튼으로 언제든 다시 볼 수 있어요.
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
