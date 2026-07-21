import { useEffect, useState } from 'react'
import david from './sketches/davidUnitedKingdom'
import creation from './sketches/creationToFlood'
import patriarchs from './sketches/patriarchsCovenant'
import exodus from './sketches/exodusToConquest'
import judges from './sketches/ageOfJudges'
import elijah from './sketches/elijahAndElisha'
import exile from './sketches/exileAndReturn'

// 투어 정차지 장면 스케치 — 투어별 모듈(frontend/src/sketches/)의 레지스트리를 집계해 렌더.
// 표준·규약은 sketches/lib.jsx 참조(task#227 확정). 등록 없는 정차지는 아무것도 안 뜸.

const SCENES = { ...david, ...creation, ...patriarchs, ...exodus, ...judges, ...elijah, ...exile }

export const hasSketch = (eventId) => Boolean(eventId && SCENES[eventId])

function TourSketch({ eventId, width = 280, reduce = false }) {
  const entry = SCENES[eventId]
  if (!entry) return null
  const { Scene } = entry
  return (
    <svg
      viewBox="0 0 120 64"
      width={width}
      height={typeof width === 'number' ? Math.round(width * 64 / 120) : undefined}
      className={reduce ? undefined : 'symbol-draw'}
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

// 카드 상단 삽화 패널 — 해설 카드에 통합(그림·설명이 한 장으로 읽히도록, 사용자 피드백 5차).
// 카메라 easeTo(400ms) 정착 후 draw 시작(그 전엔 자리만 확보해 카드 높이 점프 방지).
// 스케치 없는 정차지는 아무것도 렌더하지 않음. reduce: 딜레이 없이 최종 장면 정적 표시.
export function TourSketchPanel({ eventId }) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const [ready, setReady] = useState(reduce)
  useEffect(() => {
    if (reduce) return
    const t = setTimeout(() => setReady(true), 450)
    return () => clearTimeout(t)
  }, [reduce])

  if (!hasSketch(eventId)) return null
  const caption = SCENES[eventId]?.caption
  const desc = SCENES[eventId]?.desc
  const dark = SCENES[eventId]?.mood === 'dark'
  return (
    <div data-sketch-panel style={{
      // 무드 표현 — 종이는 항상 크림(양피지 관용구 유지, 배경 틴트는 부조화로 제거).
      // 어두운 장면은 강조색(이름표·캡션·포인트)만 금색 → 따뜻한 목탄으로 가라앉힌다.
      background: 'var(--paper)', color: 'var(--paper-ink)',
      ...(dark ? { '--paper-accent': '#5f584c' } : {}),
      borderBottom: '1px solid color-mix(in srgb, var(--paper-accent) 40%, transparent)',
      padding: '12px 16px 6px',
    }}>
      {/* draw 시작 전에도 동일 비율 자리 확보 — 카드 높이 점프 방지 */}
      <div style={{ aspectRatio: '120 / 64', width: '100%' }}>
        {ready && <TourSketch eventId={eventId} width="100%" reduce={reduce} />}
      </div>
      {(desc || caption) && (
        <div style={{ marginTop: 5, textAlign: 'center' }}>
          {/* 상황설명 — 그림이 담은 사건을 한 줄 서술(사용자 피드백) */}
          {desc && (
            <div style={{ fontFamily: 'var(--serif)', fontSize: 12.5, lineHeight: 1.45, color: 'var(--paper-ink)' }}>{desc}</div>
          )}
          {caption && (
            <div style={{
              marginTop: 2,
              fontFamily: 'var(--serif)', fontSize: 10.5, letterSpacing: '0.04em',
              color: 'var(--paper-accent)',
            }}>{caption}</div>
          )}
        </div>
      )}
    </div>
  )
}

export default TourSketch
