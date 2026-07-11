import { useState, useEffect, useRef } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { SELECT_HL, GENRE_META } from './theme'
import { MOBILE_BREAKPOINT } from './constants'

const OT_GENRE_ORDER = ['Pentateuch', 'Historical', 'Poetry-Wisdom', 'Major Prophets', 'Minor Prophets']
const NT_GENRE_ORDER = ['Gospels', 'Acts', 'Pauline Epistles', 'General Epistles', 'Revelation']

// GENRE_META는 theme.js로 이동 — SidePanel과 공유(react-refresh: 컴포넌트 파일에서 상수 export 금지)

function useIsMobile() {
  const [mobile, setMobile] = useState(() => window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches)
  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)
    const onChange = (e) => setMobile(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return mobile
}

function BookCard({ book, onSelectNode, isSelected, hideKeyVerse }) {
  const [hovered, setHovered] = useState(false)
  const themes = (book.themes || []).slice(0, 3)
  const keyVerse = !hideKeyVerse && book.keyVerseTextKo
    ? (book.keyVerseTextKo.length > 40 ? book.keyVerseTextKo.slice(0, 40) + '…' : book.keyVerseTextKo)
    : null

  return (
    <div
      onClick={() => onSelectNode(book.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: isSelected ? SELECT_HL : hovered ? 'var(--bg-2)' : 'var(--bg-1)',
        border: `1px solid ${isSelected || hovered ? 'var(--gold-dim)' : 'var(--line)'}`,
        borderRadius: 10,
        padding: 12,
        width: 140,
        cursor: 'pointer',
        flexShrink: 0,
        transition: 'border-color 0.15s, background 0.15s',
      }}
    >
      <div style={{ color: 'var(--ink)', fontFamily: 'var(--serif)', fontWeight: 600, fontSize: 14, marginBottom: book.authorKo ? 2 : 6 }}>
        {book.nameKo}
      </div>
      {book.authorKo && (
        <div style={{ color: 'var(--ink-faint)', fontSize: 11, marginBottom: 6 }}>
          {book.authorKo}{book.writtenDate ? ` · ${book.writtenDate}` : ''}
        </div>
      )}
      {themes.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: keyVerse ? 6 : 0 }}>
          {themes.map((t, i) => (
            <span
              key={i}
              style={{
                background: 'var(--bg-2)',
                color: 'var(--ink-dim)',
                fontSize: 10,
                padding: '2px 7px',
                borderRadius: 999,
              }}
            >
              {t}
            </span>
          ))}
        </div>
      )}
      {keyVerse && (
        <div style={{ color: 'var(--ink-faint)', fontSize: 11, marginTop: 6, lineHeight: 1.4 }}>
          {keyVerse}
        </div>
      )}
    </div>
  )
}

function GenreSection({ genre, books, isFirst, onSelectNode, selectedNode, hideKeyVerse }) {
  const meta = GENRE_META[genre] || { displayName: genre, description: '' }
  const sorted = [...books].sort((a, b) => (a.bookOrder ?? 0) - (b.bookOrder ?? 0))

  return (
    // data-genre: 점프 내비의 스크롤 대상 + 현재 섹션 추적 마커
    <div data-genre={genre} style={{ marginTop: isFirst ? 0 : 20 }}>
      <div style={{ marginBottom: 8 }}>
        <span style={{ color: 'var(--ink)', fontWeight: 700, fontSize: 16 }}>{meta.displayName}</span>
        {meta.description && (
          <span style={{ color: 'var(--ink-faint)', fontSize: 13, marginLeft: 8 }}>
            {meta.description}
          </span>
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {sorted.map(book => (
          <BookCard key={book.id} book={book} onSelectNode={onSelectNode} isSelected={book.id === selectedNode} hideKeyVerse={hideKeyVerse} />
        ))}
      </div>
    </div>
  )
}

function Testament({ label, genreOrder, booksByGenre, onSelectNode, selectedNode, hideKeyVerse }) {
  const genres = genreOrder.filter(g => booksByGenre[g] && booksByGenre[g].length > 0)

  return (
    <div>
      <div style={{ color: 'var(--ink)', fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 20, marginBottom: 12 }}>{label}</div>
      {genres.map((genre, i) => (
        <GenreSection
          key={genre}
          genre={genre}
          books={booksByGenre[genre]}
          isFirst={i === 0}
          onSelectNode={onSelectNode}
          selectedNode={selectedNode}
          hideKeyVerse={hideKeyVerse}
        />
      ))}
    </div>
  )
}

export default function BibleOverviewView({ onSelectNode, selectedNode }) {
  const [booksByTestamentGenre, setBooksByTestamentGenre] = useState({ OT: {}, NT: {} })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const isMobile = useIsMobile()
  // 점프 내비 — 스크롤 컨테이너·현재 보이는 장르·칩 엘리먼트 참조
  const scrollRef = useRef(null)
  const chipRefs = useRef({})
  const [activeGenre, setActiveGenre] = useState(null)

  // 현재 섹션 추적 — 상단(칩 바 아래)을 마지막으로 지난 장르 섹션을 활성으로 표시
  useEffect(() => {
    if (loading) return
    const root = scrollRef.current
    if (!root) return
    const onScroll = () => {
      const rootTop = root.getBoundingClientRect().top
      let current = null
      for (const s of root.querySelectorAll('[data-genre]')) {
        if (s.getBoundingClientRect().top - rootTop <= 64) current = s.dataset.genre
      }
      setActiveGenre(prev => current ?? prev)
    }
    onScroll()
    root.addEventListener('scroll', onScroll, { passive: true })
    return () => root.removeEventListener('scroll', onScroll)
  }, [loading])

  // 활성 칩을 칩 바 가시 영역으로 (세로 스크롤엔 영향 없음 — block: nearest)
  useEffect(() => {
    if (!activeGenre) return
    chipRefs.current[activeGenre]?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [activeGenre])

  function jumpTo(genre) {
    // scrollIntoView는 overflow:hidden인 앱 루트까지 스크롤시켜 상단 내비를 밀어낸다 — 이 컨테이너만 스크롤.
    const root = scrollRef.current
    const el = root?.querySelector(`[data-genre="${CSS.escape(genre)}"]`)
    if (!root || !el) return
    const top = el.getBoundingClientRect().top - root.getBoundingClientRect().top + root.scrollTop - 56
    root.scrollTo({ top })
  }

  useEffect(() => {
    let cancelled = false
    apiGet('/books-overview')
      .then(data => {
        if (cancelled) return
        const grouped = { OT: {}, NT: {} }
        for (const book of data) {
          const t = book.testament
          // Support both English (OT/NT) and Korean (구약/신약) testament values
          const key = (t === 'OT' || t === '구약') ? 'OT' : (t === 'NT' || t === '신약') ? 'NT' : null
          if (!key) continue
          const g = book.genre
          if (!g) continue
          if (!grouped[key][g]) grouped[key][g] = []
          grouped[key][g].push(book)
        }
        setBooksByTestamentGenre(grouped)
        setLoading(false)
      })
      .catch(err => {
        if (cancelled) return
        setError(err.message || '불러오기 실패')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: 'var(--bg-0)' }}>
        <Spinner />
      </div>
    )
  }
  if (error) {
    return (
      <div style={{ color: '#f87171', padding: 24, background: 'var(--bg-0)', height: '100%' }}>
        {/* 에러 텍스트는 대응 토큰이 없어 하드코딩 유지 */}
        오류: {error}
      </div>
    )
  }

  const totalBooks =
    Object.values(booksByTestamentGenre.OT).flat().length +
    Object.values(booksByTestamentGenre.NT).flat().length

  if (totalBooks === 0) {
    return (
      <div style={{ color: 'var(--ink-faint)', padding: 24, background: 'var(--bg-0)', height: '100%' }}>
        표시할 성경 권이 없습니다
      </div>
    )
  }

  const chipGroups = [
    { label: '구약', genres: OT_GENRE_ORDER.filter(g => booksByTestamentGenre.OT[g]?.length > 0) },
    { label: '신약', genres: NT_GENRE_ORDER.filter(g => booksByTestamentGenre.NT[g]?.length > 0) },
  ]

  return (
    <div ref={scrollRef} style={{
      background: 'var(--bg-0)',
      height: '100%',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      {/* 점프 내비 칩 바 — sticky. 배경·구분선은 전폭, 칩 내용은 본문과 같은 중앙 컬럼 정렬. 좁은 화면에선 가로 스크롤 */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 5,
        background: 'var(--bg-0)',
        borderBottom: '1px solid var(--line-strong)',
      }}>
        <div style={{
          maxWidth: 900, margin: '0 auto',
          display: 'flex', alignItems: 'center', gap: 6,
          overflowX: 'auto',
          padding: '10px 16px',
        }}>
        {chipGroups.map((group, gi) => [
          <span key={group.label} style={{
            color: 'var(--gold)', fontSize: 11, fontWeight: 700,
            letterSpacing: '0.08em', flexShrink: 0,
            marginLeft: gi > 0 ? 10 : 0,
          }}>
            {group.label}
          </span>,
          ...group.genres.map(g => {
            const active = g === activeGenre
            return (
              <button
                key={g}
                ref={el => { chipRefs.current[g] = el }}
                onClick={() => jumpTo(g)}
                style={{
                  flexShrink: 0, cursor: 'pointer', whiteSpace: 'nowrap',
                  fontSize: 12, padding: '4px 10px', borderRadius: 999,
                  border: `1px solid ${active ? 'var(--gold-dim)' : 'var(--line-strong)'}`,
                  background: active ? 'var(--bg-3)' : 'var(--bg-2)',
                  color: active ? 'var(--gold)' : 'var(--ink-dim)',
                  fontWeight: active ? 700 : 400,
                  transition: 'background 0.15s, color 0.15s',
                }}
              >
                {(GENRE_META[g] || { displayName: g }).displayName}
              </button>
            )
          }),
        ])}
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: 16 }}>
        <Testament
          label="구약"
          genreOrder={OT_GENRE_ORDER}
          booksByGenre={booksByTestamentGenre.OT}
          onSelectNode={onSelectNode}
          selectedNode={selectedNode}
          hideKeyVerse={isMobile}
        />
        <div style={{ marginTop: 32 }}>
          <Testament
            label="신약"
            genreOrder={NT_GENRE_ORDER}
            booksByGenre={booksByTestamentGenre.NT}
            onSelectNode={onSelectNode}
            selectedNode={selectedNode}
            hideKeyVerse={isMobile}
          />
        </div>
      </div>
    </div>
  )
}
