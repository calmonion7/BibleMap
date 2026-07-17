// 통일 양피지 구절 레이어 쉘(task#202 S1) — 7개 파일 9곳에 흩어져 있던 "양피지 구절 모달" 골격을 하나로 승격.
// 반응형: 뷰포트 ≤768px(MOBILE_BREAKPOINT)는 하단 시트(스와이프/ESC/배경탭 닫힘 시 슬라이드다운 재생 후 언마운트),
// >768px는 중앙 모달(닫힘은 즉시 언마운트 — 기존 결정 "닫힘은 빠를수록 좋다" 유지, ADR-0024).
// 카드 배경은 항상 양피지(--paper*, 테마 불변) — 성경 구절 본문 전용(원칙 2). children에 본문(로딩/빈 상태/절 목록)을 넣는다.
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import VerseLangTabs from './VerseLangTabs'
import { MOBILE_BREAKPOINT } from './constants'

const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT}px)`

const cardBase = {
  background: 'var(--paper)', color: 'var(--paper-ink)',
  boxShadow: 'var(--shadow-2)', padding: '18px 20px', overflowY: 'auto',
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
  const touchY = useRef(null)

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const onChange = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // 닫기 요청 — 모바일 시트는 슬라이드다운 재생 후(onAnimationEnd) 언마운트, 데스크톱 모달은 즉시(ADR-0024 유지).
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

  if (isMobile) {
    return createPortal(
      <div style={{ position: 'fixed', inset: 0, zIndex: 'var(--z-verse)' }}>
        <div className="overlay-in" onClick={requestClose} style={{ position: 'absolute', inset: 0, background: 'var(--scrim)' }} />
        <div
          role="dialog" aria-modal="true"
          className={closing ? 'sheet-out' : 'sheet-in'}
          onAnimationEnd={() => { if (closing) onClose() }}
          onTouchStart={e => { touchY.current = e.currentTarget.scrollTop > 0 ? null : e.touches[0].clientY }}
          onTouchEnd={e => {
            if (touchY.current != null && e.changedTouches[0].clientY - touchY.current > 60) requestClose()
            touchY.current = null
          }}
          style={{
            ...cardBase,
            position: 'absolute', left: 0, right: 0, bottom: 0,
            borderRadius: '16px 16px 0 0', maxHeight: '80vh',
            paddingBottom: 'calc(16px + env(safe-area-inset-bottom))',
            ...cardStyle,
          }}
        >
          {/* 그랩 핸들 — 양피지 카드라 PersonMiniCard의 ink-faint 대신 paper-accent(테마 불변 대비) */}
          <div style={{ display: 'flex', justifyContent: 'center', padding: '2px 0 10px' }}>
            <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--paper-accent)' }} />
          </div>
          {header}
          {children}
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
        style={{ ...cardBase, borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', ...cardStyle }}
      >
        {header}
        {children}
      </div>
    </div>,
    document.body,
  )
}
