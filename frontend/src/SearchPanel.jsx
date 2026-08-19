import { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'
import { apiGet } from './api'
import Spinner from './Spinner'

// 통합 검색 오버레이(task#267) — 이름(인물·장소·사건)과 구절 본문을 한 패널에서.
// 결과 클릭은 기존 화면으로 위임한다(노드는 상세/탐험, 구절은 리더의 해당 장 + 절 강조).
const DEBOUNCE_MS = 250
// 절 검색은 31k절 전수 스캔이라 서버가 2자 미만을 건너뛴다 — 안내 문구를 같은 기준으로 맞춘다.
const MIN_VERSE_QUERY = 2

const LABEL_KO = { Person: '인물', Place: '장소', Event: '사건', Book: '성경책', Period: '시대' }

export default function SearchPanel({ isMobile, onClose, onSelectNode, onSelectVerse }) {
  const [q, setQ] = useState('')
  const [res, setRes] = useState(null)      // { nodes, verses } — null이면 아직 질의 전
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  // Esc 닫기 — 패널이 열려 있는 동안만
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') { e.stopPropagation(); onClose() } }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    const term = q.trim()
    let alive = true
    // effect 동기 setState 금지 규칙 회피 — 프로젝트 관용구(WordDistributionView·ChapterReader 선례).
    if (!term) {
      Promise.resolve().then(() => { if (alive) { setRes(null); setLoading(false) } })
      return () => { alive = false }
    }
    const ctrl = new AbortController()
    Promise.resolve().then(() => { if (alive) setLoading(true) })
    const timer = setTimeout(() => {
      apiGet(`/search?q=${encodeURIComponent(term)}`, { signal: ctrl.signal })
        .then(d => { if (alive) { setRes(d); setLoading(false) } })
        .catch(e => {
          if (e?.name !== 'AbortError') {
            console.warn('[SearchPanel] 검색 실패 — 빈 결과로 폴백', e)
            if (alive) { setRes({ nodes: [], verses: [] }); setLoading(false) }
          }
        })
    }, DEBOUNCE_MS)
    return () => { alive = false; clearTimeout(timer); ctrl.abort() }
  }, [q])

  const nodes = res?.nodes ?? []
  const verses = res?.verses ?? []
  const empty = res && nodes.length === 0 && verses.length === 0

  const sectionTitle = {
    fontFamily: 'var(--serif)', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em',
    color: 'var(--gold)', margin: '14px 0 6px',
  }
  const rowStyle = {
    display: 'block', width: '100%', textAlign: 'left',
    padding: '9px 10px', borderRadius: 8, cursor: 'pointer',
    border: 'none', background: 'none', font: 'inherit',
    borderLeft: '3px solid var(--gold-dim)',
  }

  return (
    <div
      role="dialog" aria-modal="true" aria-label="통합 검색"
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 60,
        background: 'color-mix(in srgb, var(--bg-0) 78%, transparent)',
        backdropFilter: 'blur(3px)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        padding: isMobile ? '56px 10px 10px' : '76px 16px 16px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 560, maxHeight: '100%', display: 'flex', flexDirection: 'column',
          background: 'var(--bg-1)', border: '1px solid var(--line-strong)', borderRadius: 12,
          boxShadow: 'var(--shadow-2)', overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
          <Search size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
          <input
            ref={inputRef}
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="인물·장소·사건 이름 또는 구절 본문"
            aria-label="검색어"
            style={{
              flex: 1, minWidth: 0, border: 'none', outline: 'none', background: 'none',
              color: 'var(--ink)', fontSize: 15, fontFamily: 'var(--serif)',
            }}
          />
          <button
            onClick={onClose} aria-label="검색 닫기"
            style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'var(--ink-faint)', display: 'flex', padding: 2 }}
          ><X size={16} /></button>
        </div>

        <div style={{ overflowY: 'auto', padding: '4px 12px 14px' }}>
          {loading && <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 0' }}><Spinner /></div>}

          {!loading && empty && (
            <div style={{ fontSize: 13, color: 'var(--ink-dim)', textAlign: 'center', padding: '22px 0' }}>
              결과가 없어요.{q.trim().length < MIN_VERSE_QUERY && ' 구절 본문 검색은 두 글자부터예요.'}
            </div>
          )}

          {!loading && nodes.length > 0 && (
            <section data-search-section="nodes">
              <div style={sectionTitle}>인물 · 장소 · 사건</div>
              {nodes.map(n => (
                <button key={n.id} data-search-node={n.id} style={rowStyle} onClick={() => onSelectNode(n)}>
                  <span style={{ fontFamily: 'var(--serif)', fontSize: 14, color: 'var(--ink)' }}>{n.nameKo}</span>
                  <span style={{ fontSize: 11, color: 'var(--ink-faint)', marginLeft: 8 }}>{LABEL_KO[n.label] || n.label}</span>
                </button>
              ))}
            </section>
          )}

          {!loading && verses.length > 0 && (
            <section data-search-section="verses">
              <div style={sectionTitle}>구절</div>
              {verses.map(v => (
                <button key={v.verseId} data-search-verse={v.verseId} style={rowStyle} onClick={() => onSelectVerse(v)}>
                  <span style={{ fontFamily: 'var(--serif)', fontSize: 12, fontWeight: 700, color: 'var(--gold)' }}>{v.ref}</span>
                  <span style={{ display: 'block', fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5, marginTop: 2 }}>{v.textKo}</span>
                </button>
              ))}
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
