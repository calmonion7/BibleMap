import { lazy, Suspense } from 'react'
import { Play, Pause, SkipBack, SkipForward, X } from 'lucide-react'
import { TYPE_COLOR } from './theme'
// 투어 스케치는 지연 로드 — 재생 시작 시점에만 로드(task#254).
const TourSketchPanel = lazy(() => import('./tourSketches').then(m => ({ default: m.TourSketchPanel })))

// 투어 자동재생 해설 카드 (task#223, ADR-0028). 시퀀서 훅은 useTourPlayback.js로 분리(task#253).
const PURPLE = TYPE_COLOR.Book

const ctrlBtnStyle = {
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  width: 34, height: 34, borderRadius: 999, cursor: 'pointer',
  background: 'var(--bg-2)', border: '1px solid var(--line)', color: 'var(--ink)',
  transition: 'background var(--dur-fast), border-color var(--dur-fast)',
}

// 해설 카드 — 현재 사건의 seq · 인물 · 제목 · note + 컨트롤. note null이면 제목·인물만(무해설 그레이스풀).
export default function TourPlaybackCard({ stops, idx, playing, onToggle, onPrev, onNext, onExit, isMobile }) {
  const s = stops?.[idx]
  if (!s) return null
  return (
    <div style={{
      position: 'absolute', zIndex: 6,
      ...(isMobile
        ? { left: 0, right: 0, bottom: 0, borderRadius: '12px 12px 0 0' }
        : { left: '50%', transform: 'translateX(-50%)', bottom: 20, width: 'min(440px, calc(100% - 32px))', borderRadius: 12 }),
      background: 'var(--bg-1)', border: '1px solid var(--line-strong)',
      boxShadow: 'var(--shadow-2)', overflow: 'hidden',
    }}>
      {/* 본문 — 사건 전환마다 key 리마운트로 stage-in 페이드(ADR-0024 토큰, reduce 자동 존중).
          장면 스케치는 카드 상단 삽화로 통합(그림·설명 한 장, task#226 5차) — key 리마운트로 draw 재생. */}
      <div key={s.eventId ?? idx} className="stage-in">
      <Suspense fallback={null}><TourSketchPanel eventId={s.eventId} /></Suspense>
      <div style={{ padding: isMobile ? '12px 16px 4px' : '14px 18px 6px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: PURPLE, fontVariantNumeric: 'tabular-nums' }}>
            {idx + 1}/{stops.length}
          </span>
          {s.personNameKo && <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--gold)' }}>{s.personNameKo}</span>}
          <span style={{ fontSize: 14.5, fontWeight: 700, fontFamily: 'var(--serif)', color: 'var(--ink)' }}>{s.nameKo}</span>
          {s.placeNameKo && <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{s.placeNameKo}</span>}
        </div>
        {s.note && (
          <p style={{ margin: '8px 0 0', fontSize: 13.5, lineHeight: 1.65, color: 'var(--ink)', maxHeight: isMobile ? '22dvh' : 120, overflowY: 'auto' }}>
            {s.note}
          </p>
        )}
      </div>
      </div>
      {/* 컨트롤 — 이전 · 재생/일시정지 · 다음 · 종료 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: '10px 16px 12px' }}>
        <button aria-label="이전 정차지" onClick={onPrev} disabled={idx === 0} style={{ ...ctrlBtnStyle, opacity: idx === 0 ? 0.4 : 1 }}>
          <SkipBack size={15} />
        </button>
        <button aria-label={playing ? '일시정지' : '재생'} onClick={onToggle}
          style={{ ...ctrlBtnStyle, width: 42, height: 42, background: PURPLE, border: 'none', color: '#fff' }}>
          {playing ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
        </button>
        <button aria-label="다음 정차지" onClick={onNext} disabled={idx >= stops.length - 1} style={{ ...ctrlBtnStyle, opacity: idx >= stops.length - 1 ? 0.4 : 1 }}>
          <SkipForward size={15} />
        </button>
        <button aria-label="재생 종료" onClick={onExit} style={{ ...ctrlBtnStyle, marginLeft: 8 }}>
          <X size={15} />
        </button>
      </div>
    </div>
  )
}
