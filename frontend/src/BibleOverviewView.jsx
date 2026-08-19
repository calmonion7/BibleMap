import { useState, useEffect, useRef, useLayoutEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import BookSymbol from './bookSymbols'
import { SELECT_HL, GENRE_META } from './theme'
import { MOBILE_BREAKPOINT } from './constants'
import { saveScroll, loadScroll } from './scrollMemory'
import VerseLayer, { paperTextStyle } from './VerseLayer'

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

// 입장 스태거 — 세션 첫 진입만(허브와 동일 패턴)
let overviewEntrancePlayed = false

function BookCard({ book, onSelectNode, isSelected, hideKeyVerse, entrance, delayMs, readCount = 0 }) {
  const [hovered, setHovered] = useState(false)
  const themes = (book.themes || []).slice(0, 3)
  const keyVerse = !hideKeyVerse && book.keyVerseTextKo
    ? (book.keyVerseTextKo.length > 40 ? book.keyVerseTextKo.slice(0, 40) + '…' : book.keyVerseTextKo)
    : null

  return (
    <div
      className={entrance ? 'pressable card-in' : 'pressable'}
      onClick={() => onSelectNode(book.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        animationDelay: entrance ? `${delayMs}ms` : undefined,
        background: isSelected ? SELECT_HL : hovered ? 'var(--bg-2)' : 'var(--bg-1)',
        border: `1px solid ${isSelected || hovered ? 'var(--gold-dim)' : 'var(--line)'}`,
        borderRadius: 10,
        padding: 12,
        boxSizing: 'border-box',
        cursor: 'pointer',
        transition: 'border-color var(--dur-fast), background var(--dur-fast), transform var(--dur-fast) var(--ease-out)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, color: 'var(--ink)', fontFamily: 'var(--serif)', fontWeight: 600, fontSize: 14, marginBottom: book.authorKo ? 2 : 6 }}>
        {/* 책 인장(task#208) — 카드 스태거와 같은 지연으로 draw-on(세션 첫 진입만), 이후 정적 */}
        <span style={{ color: 'var(--gold)', flexShrink: 0, display: 'inline-flex' }}>
          <BookSymbol bookId={book.id} size={22} draw={entrance} delayMs={delayMs} />
        </span>
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
      {/* 읽기 진도(task#269) — 읽은 장이 0이면 렌더하지 않는다 */}
      {readCount > 0 && book.chapterCount ? (
        <div data-book-progress={`${readCount}/${book.chapterCount}`} style={{ marginTop: 8 }}>
          <div style={{ height: 3, borderRadius: 2, background: 'var(--line)', overflow: 'hidden' }}>
            <div style={{ width: `${Math.min(100, Math.round((readCount / book.chapterCount) * 100))}%`, height: '100%', background: 'var(--gold)' }} />
          </div>
          <div style={{ fontSize: 10, color: 'var(--gold)', marginTop: 3 }}>{readCount}/{book.chapterCount}장 읽음</div>
        </div>
      ) : null}
    </div>
  )
}

function GenreSection({ genre, books, isFirst, onSelectNode, selectedNode, hideKeyVerse, entrance, bookReadCount }) {
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 8, marginBottom: 16 }}>
        {sorted.map((book, i) => (
          <BookCard key={book.id} book={book} onSelectNode={onSelectNode} isSelected={book.id === selectedNode} hideKeyVerse={hideKeyVerse} readCount={bookReadCount?.(book.id) ?? 0}
            entrance={entrance} delayMs={Math.min(i * 30, 400)} />
        ))}
      </div>
    </div>
  )
}

function Testament({ label, genreOrder, booksByGenre, onSelectNode, selectedNode, hideKeyVerse, entrance, bookReadCount }) {
  const genres = genreOrder.filter(g => booksByGenre[g] && booksByGenre[g].length > 0)

  return (
    <div>
      <div style={{ color: 'var(--ink)', fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 20, marginBottom: 12 }}>{label}</div>
      {genres.map((genre, i) => (
        <GenreSection
          bookReadCount={bookReadCount}
          key={genre}
          genre={genre}
          books={booksByGenre[genre]}
          isFirst={i === 0}
          onSelectNode={onSelectNode}
          selectedNode={selectedNode}
          hideKeyVerse={hideKeyVerse}
          entrance={entrance}
        />
      ))}
    </div>
  )
}

export default function BibleOverviewView({ onSelectNode, selectedNode, verseLang, setVerseLang, bookReadCount }) {
  const [booksByTestamentGenre, setBooksByTestamentGenre] = useState({ OT: {}, NT: {} })
  // 메시아 예언→성취 스레드(task#246) — 테마별 그룹. 실패 시 빈 배열 폴백, 섹션은 0건이면 미렌더.
  const [prophecyThemes, setProphecyThemes] = useState([])
  const [prophecyLayer, setProphecyLayer] = useState(null)
  const [entrance] = useState(() => !overviewEntrancePlayed)
  useEffect(() => { overviewEntrancePlayed = true }, [])
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
      saveScroll('overview', root.scrollTop)  // 위치 캡처 — 뒤로 복원용(task#214)
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

  // 스크롤 위치 복원 — 목록 렌더(loading=false) 후 눌렀던 위치로(task#214). 장르 추적 effect보다
  // 먼저(layout effect) 실행돼 복원된 위치 기준으로 활성 장르가 계산된다.
  useLayoutEffect(() => {
    if (loading) return
    const root = scrollRef.current
    if (root) root.scrollTop = loadScroll('overview')
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

  useEffect(() => {
    let cancelled = false
    apiGet('/messianic-prophecies')
      .then(data => { if (!cancelled) setProphecyThemes(data) })
      .catch(err => { if (!cancelled) { console.warn('[BibleOverview] 메시아 예언 로드 실패', err); setProphecyThemes([]) } })
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
      <div style={{ color: 'var(--danger)', padding: 24, background: 'var(--bg-0)', height: '100%' }}>
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

  // 메시아 예언→성취 상세 — 구절 레이어(양피지) 패턴 재사용(SidePanel 인용 대조 레이어와 동일 쉘).
  function renderProphecyLayer() {
    if (!prophecyLayer) return null
    const p = prophecyLayer
    const block = (heading, rangeLabel, verses) => (
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--paper-accent)', marginBottom: 4 }}>
          {heading} — {rangeLabel}
        </div>
        {verses.map(v => (
          <div key={v.verseId} style={paperTextStyle}>{(verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'}</div>
        ))}
      </div>
    )
    return (
      <VerseLayer
        title={p.note || '메시아 예언 → 성취'}
        refLine={`${p.otRangeLabel} → ${p.ntRangeLabel}`}
        dotColor="var(--gold)"
        onClose={() => setProphecyLayer(null)}
        verseLang={verseLang}
        setVerseLang={setVerseLang}
      >
        {block('예언 (구약)', p.otRangeLabel, p.otVerses)}
        {block('성취 (신약)', p.ntRangeLabel, p.ntVerses)}
      </VerseLayer>
    )
  }

  return (
    <div ref={scrollRef} style={{
      background: 'var(--bg-0)',
      height: '100%',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      {renderProphecyLayer()}
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
                  transition: 'background var(--dur-fast), color var(--dur-fast)',
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
          bookReadCount={bookReadCount}
          label="구약"
          genreOrder={OT_GENRE_ORDER}
          booksByGenre={booksByTestamentGenre.OT}
          onSelectNode={onSelectNode}
          selectedNode={selectedNode}
          hideKeyVerse={isMobile}
          entrance={entrance}
        />
        <div style={{ marginTop: 32 }}>
          <Testament
            bookReadCount={bookReadCount}
            label="신약"
            genreOrder={NT_GENRE_ORDER}
            booksByGenre={booksByTestamentGenre.NT}
            onSelectNode={onSelectNode}
            selectedNode={selectedNode}
            hideKeyVerse={isMobile}
            entrance={entrance}
          />
        </div>

        {/* 메시아 예언→성취 스레드(task#246) — 구약·신약을 가로지르는 주제 실. 언약 리본과 같은 gold 악센트. */}
        {prophecyThemes.length > 0 && (
          <div style={{ marginTop: 32 }}>
            <div style={{ color: 'var(--ink)', fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 20, marginBottom: 12 }}>
              메시아 예언 → 성취
            </div>
            {prophecyThemes.map(group => (
              <div key={group.theme} style={{ marginTop: 16 }}>
                <div style={{ marginBottom: 8 }}>
                  <span style={{ color: 'var(--ink)', fontWeight: 700, fontSize: 16 }}>{group.theme}</span>
                  <span style={{ color: 'var(--ink-faint)', fontSize: 13, marginLeft: 8 }}>{group.pairs.length}쌍</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {group.pairs.map(p => (
                    <button
                      key={p.id}
                      onClick={() => setProphecyLayer(p)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 8, width: '100%', textAlign: 'left', font: 'inherit',
                        border: 'none', background: 'none', cursor: 'pointer',
                        borderLeft: '3px solid var(--gold)', borderRadius: 6, padding: '7px 10px',
                        transition: 'background var(--dur-fast)',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-2)' }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                    >
                      <span style={{ flexShrink: 0, fontSize: 12, fontWeight: 600, color: 'var(--ink)' }}>
                        {p.otRangeLabel} → {p.ntRangeLabel}
                      </span>
                      <span style={{ flex: 1, fontSize: 12, color: 'var(--ink-faint)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {p.note}
                      </span>
                      <span style={{
                        flexShrink: 0, fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7, fontWeight: 600,
                        border: '1px solid var(--gold-dim)', color: 'var(--gold)',
                      }}>📖 대조 ▸</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
