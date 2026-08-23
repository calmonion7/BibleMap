import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Maximize2, X } from 'lucide-react'
import INTRO_SCENES from './sketches/introMontage'
import { stepDuration } from './useTourPlayback'

// 투어 정차지 장면 스케치 — 투어별 모듈(frontend/src/sketches/)을 **투어 단위로 동적 로드**한다.
// 9모듈을 한 레지스트리로 정적 병합하던 이전 구조는 단일 대청크(425KB)를 만들었고, 밀도 상향 후엔
// maplibre 청크(1.03MB)보다 커진다 — ADR-0029가 정한 "장면 스케치는 투어별 JSX 모듈"이라는
// 코드 경계를 **번들 경계로 승격**한 것이 이 파일이다(task#287).
// 표준·저작 규약은 sketches/lib.jsx 참조. 등록 없는 정차지는 아무것도 안 뜸.
//
// 인트로 오프닝 몽타주는 5개 투어에 흩어진 5씬을 쓰므로 sketches/introMontage.jsx가 그것만
// 재수출한다 — 인트로가 투어 청크 5개를 끌어오지 않도록.
const TOUR_MODULES = {
  'creation-to-flood': () => import('./sketches/creationToFlood'),
  'patriarchs-covenant': () => import('./sketches/patriarchsCovenant'),
  'exodus-to-conquest': () => import('./sketches/exodusToConquest'),
  'age-of-judges': () => import('./sketches/ageOfJudges'),
  'david-united-kingdom': () => import('./sketches/davidUnitedKingdom'),
  'elijah-and-elisha': () => import('./sketches/elijahAndElisha'),
  'exile-and-return': () => import('./sketches/exileAndReturn'),
  'gospel-of-jesus': () => import('./sketches/gospelOfJesus'),
  'the-early-church': () => import('./sketches/theEarlyChurch'),
}

// CSS <time> 계산값 → ms. Chromium은 커스텀 프로퍼티의 계산값을 항상 원 단위(ms)로 돌려주지
// 않는다 — "500ms"로 저작해도 getComputedStyle이 ".5s"로 정규화해 돌려주는 걸 실측으로 확인했다
// (--sym-delay는 인라인으로 매겨져 ms를 유지하지만 --dur-draw-scene은 스타일시트 값이라 s로 바뀐다).
// 단순 parseFloat는 단위를 무시해 0.5를 500으로 오독한다 — 단위를 반드시 함께 읽는다.
function cssTimeMs(v) {
  const m = /^\s*(-?[\d.]+)(ms|s)?\s*$/.exec(v || '')
  if (!m) return 0
  return m[2] === 's' ? parseFloat(m[1]) * 1000 : parseFloat(m[1])
}

// letterLast(옵트인, task#306 S2): 드로인 완료 시각을 계측해 --reveal-end에 심는다 — SceneLabel.jsx의
// after= 이름표가 그 값에서 파생 지연을 계산한다(ADR 260823-112504, 수동 at= 값 대신 소스 파생).
// useLayoutEffect(페인트 전) — useEffect로 늦추면 CSS 애니메이션이 --reveal-end 기본값(0ms)으로
// 먼저 시작해 한 프레임 깜빡인다. color가 없으면(296장면 중 이 파일럿 1건 제외) 채색층이 없어
// --reveal-end == 드로인 종료(inkEnd) — 기존 동작 그대로.
//
// color(옵트인, task#306 S4, ADR 260823-112503·260823-112504): 채색층 자산 경로. 있으면 3층
// (채색층 아래 + 저작 잉크 위)을 렌더하고, 펜선 완주(inkEnd) 뒤 "압축 색칠 붓"을 마스크 안에서
// 재생한다 — 같은 저작 붓질 순서(--sym-delay)를 --wash-k로 압축해 다시 그리면 붓이 지나간 자리에
// 색이 남는다. 예산은 이 정차지의 실제 stepDuration(note)과 전역 보수 상한(GLOBAL_MIN_STEP_MS)
// 중 **더 작은 쪽**을 쓴다(적대적 리뷰, task#306 재검증 — 원래는 note만 썼다). note가 유난히 길면
// (이 파일럿 111자 → 12,990ms) 실제 예산이 plan.md 정본(11,910ms, 전 투어 최단 note 84자 기준)을
// 넘겨 버리는데, 이 파일럿이 증명해야 하는 건 "296장면으로 확대해도 안전한 페이싱"이지 이 정차지
// 하나에서 안 끊기는 페이싱이 아니다. 전역 상한이 항상 이겨 지금은 GLOBAL_MIN_STEP_MS 고정값과
// 같지만(전역 최소는 정의상 어떤 개별 note의 stepDuration보다 크지 않다), note가 더 짧은 정차지로
// 장면이 옮겨지면 그쪽 실측값이 더 작아져 자동으로 이겨 이중 방어가 된다 — 상수 복사 금지 규율은
// GLOBAL_MIN_STEP_MS 정의부의 주석 참조(살아있는 대조군이 있다).
const GLOBAL_MIN_STEP_MS = 12360 // = 9000 + min(84*40, 5000) — data/tours/*.json 전건(296정차지)
// 실측 최단 note(84자) 기준 min(stepDuration). backend/scripts/validate_scene_sketch_detail.py의
// _min_step_ms()가 검사마다 그 파일들을 다시 읽어 이 값과 대조한다(어긋나면 게이트가 빨강이 된다) —
// 그냥 복사한 매직넘버가 아니라 살아있는 대조군이 있는 상수다(ADR 260820-003946).
function SceneSvg({ Scene, width, reduce, letterLast, note, color }) {
  const svgRef = useRef(null)
  const maskId = useId()
  // 그레이스풀 강등 실측(task#306 S4): SVG <image>의 href가 404면 Chromium은 "아무것도 안 그리지"
  // 않는다 — 브라우저 기본 깨진-이미지 아이콘을 뷰박스 전체에 늘려 그리고, 이 마스크를 통과해
  // 화면에 얼룩으로 번진다(render_scene.py로 실측 확인). onError로 그 실패를 잡아 <image> 자체를
  // 다음 렌더에서 걷어내야 진짜로 "잉크 경로만 그대로 선다"가 된다.
  const [colorOk, setColorOk] = useState(true)
  const showColor = color && colorOk
  useLayoutEffect(() => {
    if (!letterLast || reduce) return
    const svg = svgRef.current
    if (!svg) return
    let maxDelay = 0
    svg.querySelectorAll('g[style*="--sym-delay"]').forEach(g => {
      const delay = cssTimeMs(getComputedStyle(g).getPropertyValue('--sym-delay'))
      if (delay > maxDelay) maxDelay = delay
    })
    const inkEnd = maxDelay + cssTimeMs(getComputedStyle(svg).getPropertyValue('--dur-draw-scene'))
    if (!showColor) {
      svg.style.setProperty('--reveal-end', `${inkEnd}ms`)
      return
    }
    // 마스크 안 Scene 복제(아래 .scene-wash)도 같은 <Label>을 다시 그리므로 querySelectorAll이
    // 실제보다 2배로 센다 — 그 복제분은 closest('.scene-wash')로 걸러낸다(index.css의
    // .scene-wash text{display:none}과 짝인 계측 쪽 수정, task#306 S4).
    const labelCount = [...svg.querySelectorAll('text.scene-label-last')]
      .filter(t => !t.closest('.scene-wash')).length
    const durBase = cssTimeMs(getComputedStyle(svg).getPropertyValue('--dur-base'))
    const durSlow = cssTimeMs(getComputedStyle(svg).getPropertyValue('--dur-slow'))
    const budget = Math.min(stepDuration(note || ''), GLOBAL_MIN_STEP_MS) - 450 // 450 = 패널 대기(B6 정본)
    // index.css .scene-label-last의 실제 종료식은 revealEnd + label-i*durBase + durSlow이고
    // label-i의 최댓값은 labelCount-1이다(0-베이스 스태거) — labelCount를 그대로 곱하면 존재하지
    // 않는 한 스태거분(durBase)을 과다 예약해 washSpan을 그만큼 깎는다(적대적 리뷰, task#306 재검증).
    const labelRsv = labelCount > 0 ? (labelCount - 1) * durBase + durSlow : 0
    const washSpan = Math.max(600, budget - inkEnd - labelRsv)
    const washDur = Math.min(700, washSpan)
    const washK = maxDelay > 0 ? (washSpan - washDur) / maxDelay : 0
    svg.style.setProperty('--wash-begin', `${inkEnd}ms`)
    svg.style.setProperty('--wash-k', `${washK}`)
    svg.style.setProperty('--wash-dur', `${washDur}ms`)
    svg.style.setProperty('--reveal-end', `${inkEnd + washSpan}ms`)
  }, [letterLast, reduce, note, showColor])
  return (
    <svg
      ref={svgRef}
      viewBox="0 0 120 64"
      width={width}
      height={typeof width === 'number' ? Math.round(width * 64 / 120) : undefined}
      // .symbol-draw가 아니라 .scene-draw(--dur-draw-scene, task#303 S1) — personSymbols/bookSymbols와
      // draw-on 속도를 분리한 장면 전용 토큰(index.css 참조).
      className={reduce ? undefined : 'scene-draw'}
      style={{ display: 'block' }}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.1"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {showColor && !reduce && (
        // 마스크 id는 useId()로 유일하게 — 카드와 확대 오버레이가 같은 장면을 동시에 렌더한다.
        // <g className="scene-wash">가 마스크 안에서 Scene을 다시 그려 압축 색칠 붓을 재생한다
        // (index.css의 .scene-wash 참조).
        <defs>
          <mask id={maskId}>
            <g className="scene-wash"><Scene reduce={reduce} /></g>
          </mask>
        </defs>
      )}
      {showColor && (
        <image href={color} x="0" y="0" width="120" height="64" mask={reduce ? undefined : `url(#${maskId})`}
          onError={() => setColorOk(false)} />
      )}
      <Scene reduce={reduce} />
    </svg>
  )
}

// 인트로 몽타주용 — 소형 재수출 레지스트리에서 동기 해석(정적 import라 대기 없음).
function TourSketch({ eventId, width = 280, reduce = false }) {
  const entry = INTRO_SCENES[eventId]
  if (!entry) return null
  return <SceneSvg Scene={entry.Scene} width={width} reduce={reduce} />
}

// 카드 상단 삽화 패널 — 해설 카드에 통합(그림·설명이 한 장으로 읽히도록, 사용자 피드백 5차).
// 카메라 easeTo(400ms) 정착 후 draw 시작(그 전엔 자리만 확보해 카드 높이 점프 방지).
// 스케치 없는 정차지는 아무것도 렌더하지 않음. reduce: 딜레이 없이 최종 장면 정적 표시.
// tourId는 어느 모듈을 내려받을지 정한다 — 정차지 하나 때문에 9투어를 다 받지 않도록(task#287).
// note: 그 정차지의 실제 재생 예산(stepDuration) 파생 입력 — SceneSvg가 채색 구간(washSpan)을
// 계산할 때 전역 보수 상한과 함께 쓴다(task#306 S4, 둘 중 더 작은 쪽이 예산이 된다).
export function TourSketchPanel({ eventId, tourId, note }) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const [ready, setReady] = useState(reduce)
  const [scenes, setScenes] = useState(null) // null = 로드 중
  const [expanded, setExpanded] = useState(false) // task#303 S2 C안 실측 — 탭하면 확대
  const expandRef = useRef(null)
  // 확대 오버레이는 새 <svg> 인스턴스라 열 때마다 draw-in을 처음부터 재생하면 사용자가 이미 본
  // 연출을 몇 초씩 다시 기다려야 한다 — 열자마자 연출 종료 시점으로 고정한다(render_scene.py와
  // 동일 기법: CSS 애니메이션은 pause+currentTime, SMIL 절정 연출은 setCurrentTime).
  useEffect(() => {
    if (!expanded) return
    const svg = expandRef.current?.querySelector('svg')
    if (!svg) return
    for (const a of svg.getAnimations({ subtree: true })) { a.pause(); a.currentTime = 20000 }
    if (svg.setCurrentTime) svg.setCurrentTime(20)
  }, [expanded])
  useEffect(() => {
    if (reduce) return
    const t = setTimeout(() => setReady(true), 450)
    return () => clearTimeout(t)
  }, [reduce])
  const load = TOUR_MODULES[tourId]
  useEffect(() => {
    // effect 본문에서 동기 setState 금지(cascading render) — 미연결 투어는 상태를 쓰지 않고
    // 아래 렌더 가드로 처리한다. 여기선 진단만 남긴다.
    if (!load) {
      console.warn('[TourSketch] 모듈이 연결되지 않은 투어', tourId)
      return undefined
    }
    let alive = true
    load()
      .then(m => { if (alive) setScenes(m.default) })
      .catch(e => {
        console.warn('[TourSketch] 투어 스케치 모듈 로드 실패', tourId, e)
        if (alive) setScenes({})
      })
    return () => { alive = false }
  }, [load, tourId])

  const entry = scenes ? scenes[eventId] : null
  // 모듈이 연결되지 않았거나, 로드가 끝났는데 키가 없으면 미저작 — 아무것도 렌더하지 않는다.
  if (!load) return null
  // 모듈 로드 전에는 패널을 내보내지 않는다 — 자리만 잡아 두고 뒤늦게 글이 들어오면 카드가
  // 그만큼 자란다(실측 1.88px). 예약 높이를 상수로 박으면 desc가 줄바꿈되는 좁은 폭에서 다시
  // 어긋나므로, 패널은 **완성된 채로 한 번에** 등장시킨다 — 정적 병합 시절과 같은 계약이고,
  // 내려받는 양이 430KB에서 투어 청크 하나로 줄어 등장은 오히려 빨라졌다.
  if (!entry) return null
  const dark = entry.mood === 'dark'
  return (
    <div data-sketch-panel style={{
      // 무드 표현 — 종이는 항상 크림(양피지 관용구 유지, 배경 틴트는 부조화로 제거).
      // 어두운 장면은 강조색(이름표·캡션·포인트)만 금색 → 따뜻한 목탄으로 가라앉힌다.
      background: 'var(--paper)', color: 'var(--paper-ink)',
      ...(dark ? { '--paper-accent': '#5f584c' } : {}),
      borderBottom: '1px solid color-mix(in srgb, var(--paper-accent) 40%, transparent)',
      padding: '12px 16px 6px',
    }}>
      {/* draw 시작 전에도 동일 비율 자리 확보 — 카드 높이 점프 방지. 완성 후에는 탭하면 확대(task#303 S2 C안 실측) */}
      <div
        role={ready ? 'button' : undefined} tabIndex={ready ? 0 : undefined}
        aria-label={ready ? '그림 확대해서 보기' : undefined}
        onClick={ready ? () => setExpanded(true) : undefined}
        onKeyDown={ready ? e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpanded(true) } } : undefined}
        style={{ position: 'relative', aspectRatio: '120 / 64', width: '100%', cursor: ready ? 'zoom-in' : undefined }}
      >
        {ready && <SceneSvg Scene={entry.Scene} width="100%" reduce={reduce} letterLast={entry.letterLast} note={note} color={entry.color} />}
        {ready && (
          // 좌하에 둔다 — 우하는 서술형 이름표(배치 레시피의 하단 띠)가 쓰는 자리라 682개 이름표 중
          // 78건이 이 버튼과 겹쳤다. B10(이름표 관통 금지)은 SVG 선분만 재므로 React 오버레이인
          // 이 버튼은 잡지 못한다 — 그래서 겹치지 않는 모서리를 고르는 것이 유일한 방어다(좌하·좌상 충돌 0건).
          <div style={{
            position: 'absolute', left: 2, bottom: 2, display: 'flex', alignItems: 'center',
            justifyContent: 'center', width: 22, height: 22, borderRadius: 999,
            background: 'color-mix(in srgb, var(--paper) 70%, transparent)', color: 'var(--paper-accent)',
          }}>
            <Maximize2 size={12} />
          </div>
        )}
      </div>
      <div style={{ marginTop: 5, textAlign: 'center' }}>
        {entry.desc && (
          <div style={{ fontFamily: 'var(--serif)', fontSize: 12.5, lineHeight: 1.45, color: 'var(--paper-ink)' }}>{entry.desc}</div>
        )}
        {entry.caption && (
          <div style={{
            marginTop: 2,
            fontFamily: 'var(--serif)', fontSize: 10.5, letterSpacing: '0.04em',
            color: 'var(--paper-accent)',
          }}>{entry.caption}</div>
        )}
      </div>
      {expanded && createPortal(
        // 조상(TourPlaybackCard)의 transform이 fixed의 containing block을 바꿔 버리므로 body에 포털
        // (VerseLayer.jsx와 동일 관용구).
        <div className="overlay-in" onClick={() => setExpanded(false)} style={{
          position: 'fixed', inset: 0, zIndex: 50, background: 'var(--scrim)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
        }}>
          <div ref={expandRef} role="dialog" aria-modal="true" aria-label="장면 그림 확대"
            className="modal-in" onClick={e => e.stopPropagation()} style={{
            maxWidth: '100%', maxHeight: '100%', overflow: 'auto', borderRadius: 12,
            // 포털은 body에 붙으므로 패널의 종이 맥락을 상속받지 못한다 — 선화가 stroke="currentColor"라
            // color를 빠뜨리면 앱 잉크색을 물려받아 크림 종이 위에서 보이지 않는다(무드 오버라이드도 함께).
            background: 'var(--paper)', color: 'var(--paper-ink)', boxShadow: 'var(--shadow-2)',
            ...(dark ? { '--paper-accent': '#5f584c' } : {}),
          }}>
            <div style={{ width: 1100, maxWidth: 'none' }}>
              <SceneSvg Scene={entry.Scene} width={1100} reduce={reduce} letterLast={entry.letterLast} note={note} color={entry.color} />
            </div>
          </div>
          <button aria-label="닫기" onClick={() => setExpanded(false)} style={{
            position: 'absolute', top: 16, right: 16, display: 'flex', alignItems: 'center',
            justifyContent: 'center', width: 36, height: 36, borderRadius: 999, cursor: 'pointer',
            background: 'var(--bg-2)', border: '1px solid var(--line)', color: 'var(--ink)',
          }}>
            <X size={17} />
          </button>
        </div>,
        document.body,
      )}
    </div>
  )
}

export default TourSketch
