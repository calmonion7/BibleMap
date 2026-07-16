import { useState, useEffect, useRef } from 'react'
import { apiGet } from './api'
import PersonSymbol from './personSymbols'

// 인물 미니 카드(task#197) — 가계도 노드 탭 시 열리는 바텀시트 요약.
// family 노드 데이터(이름·slug·role)로 즉시 렌더하고 상세(/node/{id}: 생몰·intro·구절)는 지연 fetch.
// 데이터 계층(큐레이션 → 소개 보유 → 단역, ADR-0027)에 따라 있는 필드만 자연 폴백 표시.
// 닫기: 배경 탭 / 아래 스와이프. exit는 즉시 언마운트(전역 모달 규약).

// "-1085" → "BC 1085", "30" → "AD 30"
function fmtYear(y) {
  if (!y) return null
  const s = String(y)
  return s.startsWith('-') ? `BC ${s.slice(1).split('-')[0]}` : `AD ${s.split('-')[0]}`
}

function PersonMiniCard({ node, parents = [], isFocus, onRecenter, onOpenPerson, onClose }) {
  const [detail, setDetail] = useState(null)
  const touchY = useRef(null)

  useEffect(() => {
    // 사용처가 key={cardId}로 마운트를 갈아 detail 초기값(null)이 항상 신선 — 리셋 setState 불요.
    const ctrl = new AbortController()
    apiGet(`/node/${node.id}`, { signal: ctrl.signal })
      .then(setDetail)
      .catch(e => { if (e?.name !== 'AbortError') console.warn('[PersonMiniCard] 상세 로드 실패 — 기본 정보로 폴백', e) })
    return () => ctrl.abort()
  }, [node.id])

  const props = detail?.properties || {}
  const intro = props.intro || null
  const verses = Array.isArray(props.verses) ? props.verses : []
  const born = fmtYear(props.birthYear), died = fmtYear(props.deathYear)
  const life = born || died ? [born, died].filter(Boolean).join(' – ') : null
  const father = parents.find(p => p.gender === 'Male')
  const mother = parents.find(p => p.gender === 'Female')

  const btnStyle = {
    flex: 1, padding: '10px 12px', borderRadius: 9, cursor: 'pointer', font: 'inherit',
    fontSize: 13, fontWeight: 600, border: '1px solid var(--line-strong)',
  }

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 40 }}>
      {/* 배경 딤 — 탭으로 닫기 */}
      <div className="overlay-in" onClick={onClose}
        style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)' }} />
      {/* 바텀시트 */}
      <div className="sheet-in"
        onTouchStart={e => { touchY.current = e.touches[0].clientY }}
        onTouchEnd={e => {
          if (touchY.current != null && e.changedTouches[0].clientY - touchY.current > 60) onClose()
          touchY.current = null
        }}
        style={{
          position: 'absolute', left: 0, right: 0, bottom: 0, maxHeight: '72vh', overflowY: 'auto',
          background: 'var(--bg-1)', borderRadius: '16px 16px 0 0', boxShadow: 'var(--shadow-2)',
          padding: '10px 18px calc(16px + env(safe-area-inset-bottom))', maxWidth: 560, margin: '0 auto',
        }}>
        {/* 그랩 핸들 */}
        <div style={{ display: 'flex', justifyContent: 'center', padding: '2px 0 10px' }}>
          <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--ink-faint)' }} />
        </div>

        {/* 헤더 — 인장 + 이름(한/영) + role */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <PersonSymbol slug={node.slug} size={46} draw style={{ color: 'var(--gold)', flexShrink: 0 }} />
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontFamily: 'var(--serif)', fontSize: 19, fontWeight: 700, color: 'var(--ink)' }}>{node.nameKo}</span>
              {node.name && node.name !== node.nameKo && (
                <span style={{ fontSize: 12, color: 'var(--ink-faint)' }}>{node.name}</span>
              )}
            </div>
            {(node.role || props.role) && (
              <div style={{ fontSize: 12.5, color: 'var(--gold)', marginTop: 2 }}>{node.role || props.role}</div>
            )}
          </div>
        </div>

        {/* 생몰 · 부모 */}
        {(life || father || mother) && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 16px', marginTop: 12, fontSize: 12, color: 'var(--ink-dim)' }}>
            {life && <span>{life}</span>}
            {father && <span>아버지 · <b style={{ fontWeight: 600 }}>{father.nameKo}</b></span>}
            {mother && <span>어머니 · <b style={{ fontWeight: 600 }}>{mother.nameKo}</b></span>}
          </div>
        )}

        {/* 소개 — 서사 인물만 보유(단역은 role 한줄이 전부, ADR-0027) */}
        {intro && (
          <p style={{
            margin: '12px 0 0', fontSize: 13.5, lineHeight: 1.65, color: 'var(--ink)',
            display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>
            {intro}
          </p>
        )}

        {/* 언급 구절 칩 */}
        {verses.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
            {verses.slice(0, 6).map(v => (
              <span key={v.ref} title={v.textKo || ''} style={{
                padding: '3px 9px', borderRadius: 999, fontSize: 11,
                border: '1px solid var(--line)', color: 'var(--ink-dim)', background: 'var(--bg-0)',
              }}>
                {v.ref}
              </span>
            ))}
          </div>
        )}

        {/* 동작 — 재중심화는 카드 경유로만(노드 직접 탭 재중심화 제거, task#197) */}
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          {!isFocus && (
            <button onClick={() => { onRecenter(node.id); onClose() }} style={{
              ...btnStyle, color: 'var(--bg-0)', background: 'var(--gold)', border: 'none',
            }}>
              이 인물 중심으로 보기
            </button>
          )}
          <button onClick={() => onOpenPerson(node.id)} style={{
            ...btnStyle, color: 'var(--gold)', background: 'var(--bg-2)',
          }}>
            인물 페이지 →
          </button>
        </div>
      </div>
    </div>
  )
}

export default PersonMiniCard
