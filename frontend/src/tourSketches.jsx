import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Maximize2, X } from 'lucide-react'
import INTRO_SCENES from './sketches/introMontage'

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

function SceneSvg({ Scene, width, reduce }) {
  return (
    <svg
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
export function TourSketchPanel({ eventId, tourId }) {
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
        {ready && <SceneSvg Scene={entry.Scene} width="100%" reduce={reduce} />}
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
              <SceneSvg Scene={entry.Scene} width={1100} reduce={reduce} />
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
