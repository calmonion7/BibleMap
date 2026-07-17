// 통일 양피지 구절 레이어 쉘(task#202 S1) — 7개 파일 9곳에 흩어져 있던 "양피지 구절 모달" 골격을 하나로 승격.
// 반응형: 뷰포트 ≤768px(MOBILE_BREAKPOINT)는 하단 시트, >768px는 중앙 모달(닫힘은 즉시 언마운트 — "닫힘은 빠를수록 좋다" 유지).
// 헤더(핸들·제목·한/영·×)는 고정 존, 본문(children)만 스크롤 — 긴 구절에서도 닫기·언어 전환이 항상 손에 닿는다.
// 모바일 닫기 제스처는 핸들·헤더 존 전용 드래그(손가락 추종 → 80px 초과 시 닫힘, 미만 스프링백) — 본문 스크롤과 완전 분리.
// 카드 배경은 항상 양피지(--paper*, 테마 불변) — 성경 구절 본문 전용(원칙 2). children에 본문(로딩/빈 상태/절 목록)을 넣는다.
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import VerseLangTabs from './VerseLangTabs'
import { MOBILE_BREAKPOINT } from './constants'

const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT}px)`
const CLOSE_DRAG_PX = 80

// 패딩·스크롤은 헤더/본문 존이 각자 소유 — 카드 자체는 껍데기만.
const cardBase = {
  background: 'var(--paper)', color: 'var(--paper-ink)', boxShadow: 'var(--shadow-2)',
  display: 'flex', flexDirection: 'column', overflow: 'hidden',
}

// 구절 본문 공통 스타일 — 기존 파일들의 15/15.5 fontSize 불일치를 15.5로 통일하는 기준.
export const paperTextStyle = { fontFamily: 'var(--serif)', fontSize: 15.5, lineHeight: 1.8, color: 'var(--paper-ink)' }

// 다권 pill 탭(JourneyList 기존 스타일 승격). activeIdx는 배열 인덱스가 아니라 활성 book의 bookId(선택 식별자).
export function VerseBookTabs({ books, activeIdx, onSelect }) {
  if (!books || books.length < 2) return null
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
      {books.map(b => {
        const sel = b.bookId === activeIdx
        return (
          <button key={b.bookId} onClick={() => onSelect(b.bookId)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 11, padding: '1px 8px',
              borderRadius: 999, lineHeight: 1.7, fontWeight: 600, cursor: 'pointer',
              border: '1px solid var(--paper-accent)',
              background: sel ? 'var(--paper-accent)' : 'transparent',
              color: sel ? 'var(--paper)' : 'var(--paper-accent)',
            }}
          >{b.bookNameKo || b.bookId}</button>
        )
      })}
    </div>
  )
}

export default function VerseLayer({
  title, titleColor, refLine, dotColor, onClose, verseLang, setVerseLang, hideLangTabs, cardStyle, children,
}) {
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)
  const [closing, setClosing] = useState(false)
  const [entered, setEntered] = useState(false)   // sheet-in(fill 있는 keyframe)이 인라인 transform을 덮지 않도록 종료 후 클래스 제거
  const [dragY, setDragY] = useState(0)   // 시각적 transform 전용
  const dragFrom = useRef(null)
  const dragPx = useRef(0)   // 닫기 판정 전용 — state 클로저는 연속 터치에서 리렌더보다 늦을 수 있다

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // 닫기 요청 — 모바일 시트는 슬라이드다운(transform 트랜지션) 후 언마운트, 데스크톱 모달은 즉시.
  const requestClose = () => { isMobile ? setClosing(true) : onClose() }

  // ESC — 마운트 중에만(document 리스너). deps 없이 매 렌더 재구독해 최신 isMobile/onClose를 잡는다(레이어 수명이 짧아 비용 무시 가능).
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') requestClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  })

  const header = (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: refLine ? 4 : 10 }}>
        {dotColor && <span style={{ width: 10, height: 10, borderRadius: '50%', background: dotColor, flexShrink: 0 }} />}
        <span style={{ fontWeight: 700, fontSize: 15, flex: 1, fontFamily: 'var(--serif)', color: titleColor }}>{title}</span>
        {!hideLangTabs && <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />}
        <button onClick={requestClose} aria-label="닫기" style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}>×</button>
      </div>
      {refLine && <div style={{ fontSize: 12, color: 'var(--paper-accent)', marginBottom: 8 }}>{refLine}</div>}
    </div>
  )

  // eco: 시트/모달은 존별 패딩 고정이라 cardStyle의 padding 오버라이드는 무시(랭킹 모달 16/18↔기본 18/20 차이는 시각적으로 무의미)
  const { padding: _pad, ...cardRest } = cardStyle || {}

  if (isMobile) {
    const dragging = dragFrom.current != null
    return createPortal(
      <div style={{ position: 'fixed', inset: 0, zIndex: 'var(--z-verse)' }}>
        <div className="overlay-in" onClick={requestClose} style={{ position: 'absolute', inset: 0, background: 'var(--scrim)' }} />
        <div
          role="dialog" aria-modal="true"
          className={entered ? undefined : 'sheet-in'}
          onAnimationEnd={() => setEntered(true)}
          onTransitionEnd={e => { if (closing && e.target === e.currentTarget) onClose() }}
          style={{
            ...cardBase,
            position: 'absolute', left: 0, right: 0, bottom: 0,
            borderRadius: '16px 16px 0 0', maxHeight: '80vh',
            transform: closing ? 'translateY(105%)' : `translateY(${dragY}px)`,
            transition: dragging ? 'none' : 'transform var(--dur-fast) var(--ease-drawer)',
            ...cardRest,
          }}
        >
          {/* 드래그 존 — 핸들+헤더. 본문 스크롤과 분리돼 스크롤 위치와 무관하게 언제든 끌어내려 닫는다. */}
          <div
            onTouchStart={e => { dragFrom.current = e.touches[0].clientY }}
            onTouchMove={e => {
              if (dragFrom.current == null) return
              const dy = Math.max(0, e.touches[0].clientY - dragFrom.current)
              dragPx.current = dy
              setDragY(dy)
            }}
            onTouchEnd={() => {
              const passed = dragPx.current > CLOSE_DRAG_PX
              dragFrom.current = null
              dragPx.current = 0
              if (passed) setClosing(true)
              else setDragY(0)   // 스프링백
            }}
            style={{ padding: '18px 20px 0', touchAction: 'none', flexShrink: 0 }}
          >
            {/* 그랩 핸들 — 양피지 카드라 PersonMiniCard의 ink-faint 대신 paper-accent(테마 불변 대비) */}
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2px 0 10px' }}>
              <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--paper-accent)' }} />
            </div>
            {header}
          </div>
          <div style={{ overflowY: 'auto', minHeight: 0, padding: '0 20px calc(16px + env(safe-area-inset-bottom))' }}>
            {children}
          </div>
        </div>
      </div>,
      document.body,
    )
  }

  return createPortal(
    <div className="overlay-in" onClick={requestClose} style={{ position: 'fixed', inset: 0, zIndex: 'var(--z-verse)', background: 'var(--scrim)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div
        role="dialog" aria-modal="true"
        onClick={e => e.stopPropagation()}
        className="modal-in"
        style={{ ...cardBase, borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', ...cardRest }}
      >
        <div style={{ padding: '18px 20px 0', flexShrink: 0 }}>{header}</div>
        <div style={{ overflowY: 'auto', minHeight: 0, padding: '0 20px 18px' }}>{children}</div>
      </div>
    </div>,
    document.body,
  )
}
